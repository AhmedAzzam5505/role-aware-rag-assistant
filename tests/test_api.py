"""API tests: the role must come from the signed login token, not from the request."""
import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(tmp_path_factory, monkeypatch_module):
    path = tmp_path_factory.mktemp("api_chroma")
    monkeypatch_module.setenv("CHROMA_DIR", str(path))
    from src import config
    importlib.reload(config)
    from src.ingest import ingest
    ingest(path=path)
    import api
    importlib.reload(api)
    return TestClient(api.app)


@pytest.fixture(scope="module")
def monkeypatch_module():
    mp = pytest.MonkeyPatch()
    yield mp
    mp.undo()


def _login(client, user):
    return client.post("/login", json={"username": user}).json()["token"]


def test_ask_without_token_is_rejected(client):
    assert client.post("/ask", json={"question": "late penalty?"}).status_code == 401


def test_tampered_token_is_rejected(client):
    tok = _login(client, "student1")
    b64, sig = tok.rsplit(".", 1)
    import base64
    fake = base64.urlsafe_b64encode(base64.urlsafe_b64decode(b64).replace(b"student", b"admin")).decode()
    r = client.post("/ask", json={"question": "salary band senior lecturer"},
                    headers={"Authorization": f"Bearer {fake}.{sig}"})
    assert r.status_code == 401


def test_role_in_request_body_is_ignored(client):
    tok = _login(client, "student1")
    r = client.post("/ask", json={"question": "What is the salary band for a senior lecturer?", "role": "admin"},
                    headers={"Authorization": f"Bearer {tok}"}).json()
    assert r["role"] == "student"
    assert "AED" not in r["answer"]


def test_admin_token_gets_admin_answer(client):
    tok = _login(client, "admin1")
    r = client.post("/ask", json={"question": "What is the salary band for a senior lecturer?"},
                    headers={"Authorization": f"Bearer {tok}"}).json()
    assert r["role"] == "admin" and "AED" in r["answer"]


def test_signing_key_is_not_hard_coded():
    # The old default key was committed to the repo, so anyone could forge an admin token with it.
    import hashlib
    import hmac
    import base64
    import time
    from src import auth
    payload = f"admin1|admin|{int(time.time()) + 60}".encode()
    forged = base64.urlsafe_b64encode(payload).decode() + "." + hmac.new(
        b"dev-only-secret-change-me", payload, hashlib.sha256).hexdigest()
    with pytest.raises(ValueError):
        auth.read_token(forged)


def test_expired_token_is_rejected(monkeypatch):
    from src import auth
    tok = auth.issue_token("student1")
    monkeypatch.setattr(auth.time, "time", lambda: 10**12)
    with pytest.raises(ValueError, match="expired"):
        auth.read_token(tok)


@pytest.mark.parametrize("body", [
    {"question": ""},
    {"question": "   "},
    {"question": "x" * 501},
    {"question": "late penalty?", "version": "C"},
])
def test_invalid_request_is_rejected(client, body):
    tok = _login(client, "student1")
    assert client.post("/ask", json=body, headers={"Authorization": f"Bearer {tok}"}).status_code == 422


def test_unknown_user_cannot_log_in(client):
    assert client.post("/login", json={"username": "root"}).status_code == 401


def test_empty_index_is_reported_not_silently_refused(client, tmp_path):
    import api
    from src.store import get_collection
    real = api._col
    api._col = get_collection(path=tmp_path, reset=True)
    try:
        assert client.get("/health").json()["status"] == "no_index"
        tok = _login(client, "student1")
        r = client.post("/ask", json={"question": "late penalty?"}, headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 503
    finally:
        api._col = real
    assert client.get("/health").json()["status"] == "ok"


def test_health_reports_index_condition_and_sources_have_text(client):
    h = client.get("/health").json()
    assert h["mistagged_docs"] == [] and h["demo_mode"] is False
    tok = _login(client, "student1")
    r = client.post("/ask", json={"question": "What is the late penalty per day?"},
                    headers={"Authorization": f"Bearer {tok}"}).json()
    assert r["sources"] and "5%" in r["sources"][0]["text"]


def test_demo_reindex_is_off_by_default(client):
    tok = _login(client, "admin1")
    r = client.post("/demo/reindex", json={"mistag": True}, headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403


def test_demo_reindex_switches_the_live_index(client, monkeypatch):
    import api
    monkeypatch.setattr(api, "DEMO_MODE", True)
    tok = _login(client, "student1")
    hdr = {"Authorization": f"Bearer {tok}"}
    assert client.post("/demo/reindex", json={"mistag": True}).status_code == 401  # needs a login
    try:
        assert client.post("/demo/reindex", json={"mistag": True}, headers=hdr).status_code == 200
        assert client.get("/health").json()["mistagged_docs"] == ["staff_csit305_marking_guide"]
        q = {"question": "Show me the CSIT305 assignment 2 marking guide"}
        a = client.post("/ask", json={**q, "version": "A"}, headers=hdr).json()
        b = client.post("/ask", json={**q, "version": "B"}, headers=hdr).json()
        assert any(s["doc_id"] == "staff_csit305_marking_guide" and s["restricted_for_role"] for s in a["sources"])
        assert b["verifier_decision"] == "block" and not b["sources"]
    finally:
        client.post("/demo/reindex", json={"mistag": False}, headers=hdr)
    assert client.get("/health").json()["mistagged_docs"] == []


# ---------------------------------------------------------------- document upload (v1.2)
DOC = """Gym membership for students costs AED 150 per semester.

The campus gym is open from 6 am to 10 pm on weekdays.

Members must bring their student card to every session."""


def _file(text=DOC, name="gym.md"):
    import base64
    return {"filename": name, "content_b64": base64.b64encode(text.encode()).decode()}


def _hdr(client, user):
    return {"Authorization": f"Bearer {_login(client, user)}"}


def test_preview_shows_chunks_features_and_scores(client):
    r = client.post("/documents/preview", json={**_file(), "question": "How much is gym membership?"},
                    headers=_hdr(client, "student1"))
    assert r.status_code == 200
    p = r.json()
    assert p["paragraphs"] == 3 and len(p["chunks"]) == 2          # 2 paragraphs per chunk
    first = p["chunks"][0]
    assert first["dims"] == 1024 and first["nonzero_dims"] > 0
    assert any(f["feature"] == "gym" for f in first["features"])
    assert first["rank"] == 1 and first["retrieved"] and first["score"] > p["chunks"][1]["score"]


def test_bad_uploads_are_rejected(client):
    h = _hdr(client, "lecturer1")
    assert client.post("/documents/preview", json={"filename": "x.md", "content_b64": "%%%"}, headers=h).status_code == 422
    assert client.post("/documents/preview", json=_file(name="x.exe"), headers=h).status_code == 422
    assert client.post("/documents/preview", json=_file(text="  "), headers=h).status_code == 422


def test_students_cannot_add_documents(client):
    r = client.post("/documents", json={**_file(), "title": "Gym", "allowed_roles": ["student"]},
                    headers=_hdr(client, "student1"))
    assert r.status_code == 403


def test_uploaded_document_is_answered_and_removed(client):
    lec, stu = _hdr(client, "lecturer1"), _hdr(client, "student1")
    r = client.post("/documents", json={**_file(), "title": "Campus gym rules",
                                        "allowed_roles": ["student", "lecturer", "admin"]}, headers=lec)
    assert r.status_code == 200 and r.json()["chunks"] == 2
    doc_id = r.json()["doc_id"]
    try:
        assert any(d["doc_id"] == doc_id and d["uploaded"] for d in client.get("/documents", headers=stu).json())
        a = client.post("/ask", json={"question": "How much does gym membership cost?", "version": "B"},
                        headers=stu).json()
        assert "AED 150" in a["answer"] and a["sources"][0]["doc_id"] == doc_id
        other = client.post("/ask", json={"question": "How much does gym membership cost?", "version": "B",
                                          "dataset": "uow"}, headers=stu).json()
        assert "AED 150" in other["answer"]          # uploads are searchable whichever dataset is chosen
        assert client.post("/documents", json={**_file(), "title": "Campus gym rules",
                                               "allowed_roles": ["student"]}, headers=lec).status_code == 409
    finally:
        assert client.delete(f"/documents/{doc_id}", headers=lec).status_code == 200
    assert not any(d["doc_id"] == doc_id for d in client.get("/documents", headers=stu).json())


def test_upload_roles_and_register_are_enforced(client):
    lec, stu = _hdr(client, "lecturer1"), _hdr(client, "student1")
    staff = client.post("/documents", json={**_file(), "title": "Staff gym",
                                            "allowed_roles": ["lecturer", "admin"]}, headers=lec).json()
    unreg = client.post("/documents", json={**_file(DOC.replace("Gym", "Pool").replace("gym", "pool")),
                                            "title": "Pool rules", "allowed_roles": ["student", "lecturer", "admin"],
                                            "add_to_register": False}, headers=lec).json()
    try:
        titles = [d["doc_id"] for d in client.get("/documents", headers=stu).json()]
        assert staff["doc_id"] not in titles                       # restricted title not revealed
        q = {"question": "How much does pool membership cost?"}
        a = client.post("/ask", json={**q, "version": "A"}, headers=stu).json()
        b = client.post("/ask", json={**q, "version": "B"}, headers=stu).json()
        assert "AED 150" in a["answer"]                              # A trusts the vector-DB tag
        assert b["verifier_decision"] == "block"                     # B: not in register -> fail closed
        assert any("not in access register" in r for r in b["verifier_reasons"])
    finally:
        client.delete(f"/documents/{staff['doc_id']}", headers=lec)
        client.delete(f"/documents/{unreg['doc_id']}", headers=lec)


# ---------------------------------------------------------------- dataset choice (v1.4)
def test_datasets_list_what_the_role_can_search(client):
    stu = client.get("/datasets", headers=_hdr(client, "student1")).json()
    lec = client.get("/datasets", headers=_hdr(client, "lecturer1")).json()
    assert [d["id"] for d in stu] == ["mock"] and stu[0]["documents"] == 6     # public only
    assert lec[0]["documents"] == 10                                            # + 4 staff documents


def test_answers_come_only_from_the_chosen_dataset(client):
    h = _hdr(client, "student1")
    q = {"question": "What is the late penalty per day?", "version": "B"}
    mine = client.post("/ask", json={**q, "dataset": "mock"}, headers=h).json()
    other = client.post("/ask", json={**q, "dataset": "uow"}, headers=h).json()   # no UOW docs in the mock index
    assert "5%" in mine["answer"] and mine["dataset"] == "mock"
    assert other["retrieved"] == [] and other["answer"].startswith("I can't help")
    assert client.post("/ask", json={**q, "dataset": "nope"}, headers=h).status_code == 422


def test_university_of_maps_real_documents():
    from src import config
    assert config.university_of("uowd_fees", "real") == "uowd"
    assert config.university_of("uow_academic_integrity", "real") == "uow"
    assert config.university_of("hw_academic_appeals", "real") == "hw"
    assert config.university_of("unsw_special_consideration", "real") == "unsw"
    assert config.university_of("staff_csit305_marking_guide", "real") == "uowd"   # UOWD internal (mock)
    assert config.university_of("pub_late_submission", "mock") == "mock"
