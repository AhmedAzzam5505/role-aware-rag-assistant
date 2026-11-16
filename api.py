"""FastAPI backend.

    uvicorn api:app --reload
    POST /login {"username": "student1"}                    -> {"token": ..., "role": "student"}
    POST /ask   {"question": "...", "version": "B"}  header: Authorization: Bearer <token>
    GET  /health                                            -> mode, chunks, mis-tagged documents
    POST /demo/reindex {"mistag": true}   only if DEMO_MODE=1; rebuilds the index for live demos
"""
import os
import threading
from typing import Literal

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, field_validator

from src import config
from src.auth import USERS, issue_token, read_token
from src.ingest import MISTAG_DOC, ingest, read_index_info
from src.orchestrator import Orchestrator
from src.store import get_collection

app = FastAPI(title="Role-Aware Multi-Agent RAG Assistant")
# Demo controls (re-building the index from the web page) are off unless DEMO_MODE=1.
DEMO_MODE = os.getenv("DEMO_MODE", "0") == "1"
_lock = threading.Lock()


def _load(col):
    global _col, _orch
    _col = col
    _orch = {"A": Orchestrator(col, use_verifier=False), "B": Orchestrator(col, use_verifier=True)}


_load(get_collection())


MAX_QUESTION_CHARS = 500


class AskRequest(BaseModel):
    question: str = Field(max_length=MAX_QUESTION_CHARS)
    version: Literal["A", "B"] = "B"

    @field_validator("question")
    @classmethod
    def not_blank(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("question must not be empty")
        return v


class LoginRequest(BaseModel):
    username: str


class ReindexRequest(BaseModel):
    mistag: bool = False


def _session(authorization):
    try:
        return read_token(authorization.removeprefix("Bearer ").strip())
    except ValueError as e:
        raise HTTPException(401, f"not logged in: {e}")


@app.post("/login")
def login(req: LoginRequest):
    if req.username not in USERS:
        raise HTTPException(401, "unknown user")
    return {"username": req.username, "role": USERS[req.username], "token": issue_token(req.username)}


@app.post("/ask")
def ask(req: AskRequest, authorization: str = Header(default="")):
    session = _session(authorization)
    if _col.count() == 0:
        # Without this the API answered every question with the neutral reply, which looks
        # like a working refusal and hid the real problem (nobody had run the ingestion).
        raise HTTPException(503, "index is empty: run `python -m src.ingest` first")
    # The role comes from the signed session, never from the request body or the question.
    with _lock:
        return _orch[req.version].ask(req.question, session["role"])


@app.get("/health")
def health():
    n = _col.count()
    info = read_index_info()
    return {"status": "ok" if n else "no_index", "mode": config.MODE, "chunks": n,
            "mistagged_docs": info.get("mistagged_docs"), "demo_mode": DEMO_MODE}


@app.post("/demo/reindex")
def demo_reindex(req: ReindexRequest, authorization: str = Header(default="")):
    """Rebuild the index normally or with the marking guide mis-tagged, for live demos only."""
    if not DEMO_MODE:
        raise HTTPException(403, "demo controls are disabled (start the API with DEMO_MODE=1)")
    _session(authorization)
    with _lock:
        col, n = ingest(mistag=req.mistag)
        _load(col)
    return {"chunks": n, "mistagged_docs": [MISTAG_DOC] if req.mistag else []}
