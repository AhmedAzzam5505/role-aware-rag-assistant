"""FastAPI backend.

    uvicorn api:app --reload
    POST /login {"username": "student1"}                    -> {"token": ..., "role": "student"}
    POST /ask   {"question": "...", "version": "B"}  header: Authorization: Bearer <token>
"""
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from src import config
from src.auth import USERS, issue_token, read_token
from src.orchestrator import Orchestrator
from src.store import get_collection

app = FastAPI(title="Role-Aware Multi-Agent RAG Assistant")
_col = get_collection()
_orch = {"A": Orchestrator(_col, use_verifier=False), "B": Orchestrator(_col, use_verifier=True)}


class AskRequest(BaseModel):
    question: str
    version: str = "B"


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
    if req.version not in _orch:
        raise HTTPException(400, "version must be A or B")
    # The role comes from the signed session, never from the request body or the question.
    return _orch[req.version].ask(req.question, session["role"])


@app.get("/health")
def health():
    return {"status": "ok", "mode": config.MODE, "chunks": _col.count()}
