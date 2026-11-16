"""FastAPI backend.

    uvicorn api:app --reload
    POST /login {"username": "student1"}                    -> {"token": ..., "role": "student"}
    POST /ask   {"question": "...", "version": "B"}  header: Authorization: Bearer <token>
"""
from typing import Literal

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, field_validator

from src import config
from src.auth import USERS, issue_token, read_token
from src.orchestrator import Orchestrator
from src.store import get_collection

app = FastAPI(title="Role-Aware Multi-Agent RAG Assistant")
_col = get_collection()
_orch = {"A": Orchestrator(_col, use_verifier=False), "B": Orchestrator(_col, use_verifier=True)}


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


@app.post("/login")
def login(req: LoginRequest):
    if req.username not in USERS:
        raise HTTPException(401, "unknown user")
    return {"username": req.username, "role": USERS[req.username], "token": issue_token(req.username)}


@app.post("/ask")
def ask(req: AskRequest, authorization: str = Header(default="")):
    try:
        session = read_token(authorization.removeprefix("Bearer ").strip())
    except ValueError as e:
        raise HTTPException(401, f"not logged in: {e}")
    if _col.count() == 0:
        # Without this the API answered every question with the neutral reply, which looks
        # like a working refusal and hid the real problem (nobody had run the ingestion).
        raise HTTPException(503, "index is empty: run `python -m src.ingest` first")
    # The role comes from the signed session, never from the request body or the question.
    return _orch[req.version].ask(req.question, session["role"])


@app.get("/health")
def health():
    n = _col.count()
    return {"status": "ok" if n else "no_index", "mode": config.MODE, "chunks": n}
