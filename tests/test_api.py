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
