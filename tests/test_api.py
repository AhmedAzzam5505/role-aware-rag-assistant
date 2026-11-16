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
