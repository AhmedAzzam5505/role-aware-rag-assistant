"""FastAPI backend.

    uvicorn api:app --reload
    POST /ask  {"question": "...", "role": "student", "version": "B"}
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src import config
from src.orchestrator import Orchestrator
from src.store import get_collection

app = FastAPI(title="Role-Aware Multi-Agent RAG Assistant")
_col = get_collection()
_orch = {"A": Orchestrator(_col, use_verifier=False), "B": Orchestrator(_col, use_verifier=True)}

# Demo accounts. In a real deployment the role would come from university single sign-on.
USERS = {"student1": "student", "lecturer1": "lecturer", "admin1": "admin"}


class AskRequest(BaseModel):
    question: str
    role: str
    version: str = "B"


class LoginRequest(BaseModel):
    username: str


@app.post("/login")
def login(req: LoginRequest):
    if req.username not in USERS:
        raise HTTPException(401, "unknown user")
    return {"username": req.username, "role": USERS[req.username]}


@app.post("/ask")
def ask(req: AskRequest):
    if req.role not in config.ROLES:
        raise HTTPException(400, "unknown role")
    if req.version not in _orch:
        raise HTTPException(400, "version must be A or B")
    return _orch[req.version].ask(req.question, req.role)


@app.get("/health")
def health():
    return {"status": "ok", "mode": config.MODE, "chunks": _col.count()}
