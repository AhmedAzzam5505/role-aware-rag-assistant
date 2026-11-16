"""FastAPI backend.

    uvicorn api:app --reload
    POST /login {"username": "student1"}                    -> {"token": ..., "role": "student"}
    POST /ask   {"question": "...", "version": "B"}  header: Authorization: Bearer <token>
    GET  /health                                            -> mode, chunks, mis-tagged documents
    POST /demo/reindex {"mistag": true}   only if DEMO_MODE=1; rebuilds the index for live demos
    GET  /documents                        documents the caller's role can see
    POST /documents/preview                chunks + embeddings of an uploaded file (nothing stored)
    POST /documents                        add an uploaded file to the live index (lecturer/admin)
    DELETE /documents/{doc_id}             remove an uploaded document (lecturer/admin)
"""
import base64
import binascii
import os
import threading
from typing import List, Literal, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, field_validator

from src import config
from src.auth import USERS, issue_token, read_token
from src.agents.verifier import load_register
from src.ingest import MISTAG_DOC, ingest, read_index_info
from src.orchestrator import Orchestrator
from src.store import get_collection
from src import uploads

app = FastAPI(title="Role-Aware Multi-Agent RAG Assistant")
# Demo controls (re-building the index from the web page) are off unless DEMO_MODE=1.
DEMO_MODE = os.getenv("DEMO_MODE", "0") == "1"
_lock = threading.Lock()
_register = load_register()
_uploads = {}  # doc_id -> title, for documents added from the web page


def _load(col):
    global _col, _orch, _register
    _col = col
    _orch = {"A": Orchestrator(col, use_verifier=False), "B": Orchestrator(col, use_verifier=True)}
    _register = load_register()  # a rebuilt index has no uploads, so neither does the register
    _uploads.clear()


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


class FileRequest(BaseModel):
    filename: str = Field(max_length=200)
    content_b64: str


class PreviewRequest(FileRequest):
    question: Optional[str] = Field(default=None, max_length=MAX_QUESTION_CHARS)


class UploadRequest(FileRequest):
    title: str = Field(min_length=1, max_length=120)
    allowed_roles: List[Literal["student", "lecturer", "admin"]] = Field(min_length=1)
    add_to_register: bool = True


def _paragraphs(req):
    try:
        data = base64.b64decode(req.content_b64, validate=True)
        return uploads.extract_paragraphs(req.filename, data)
    except (binascii.Error, ValueError) as e:
        raise HTTPException(422, str(e))


def _staff(authorization):
    session = _session(authorization)
    if session["role"] not in ("lecturer", "admin"):
        raise HTTPException(403, "only lecturers and admins can add or remove documents")
    return session


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
        res = _orch[req.version].ask(req.question, session["role"])
    # For the research demo: flag any cited source the role may not see (only ever true when
    # Version A shows a mis-tagged document). The register itself is never sent to the client.
    for s in res["sources"]:
        s["restricted_for_role"] = session["role"] not in _register.get(s["doc_id"], set())
    return res


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


@app.get("/documents")
def list_documents(authorization: str = Header(default="")):
    """Documents the caller's role may retrieve (titles of others are not revealed)."""
    role = _session(authorization)["role"]
    docs = {}
    for md in _col.get(where={f"role_{role}": True}, include=["metadatas"])["metadatas"]:
        d = docs.setdefault(md["doc_id"], {"doc_id": md["doc_id"], "title": md["title"], "chunks": 0,
                                           "allowed_roles": md["allowed_roles"].split(","),
                                           "uploaded": md["doc_id"] in _uploads})
        d["chunks"] += 1
    return sorted(docs.values(), key=lambda d: (not d["uploaded"], d["doc_id"]))


@app.post("/documents/preview")
def preview_document(req: PreviewRequest, authorization: str = Header(default="")):
    _session(authorization)
    paras = _paragraphs(req)
    try:
        return uploads.preview(paras, req.question.strip() if req.question else None)
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.post("/documents")
def add_document(req: UploadRequest, authorization: str = Header(default="")):
    _staff(authorization)
    paras = _paragraphs(req)
    doc_id = uploads.slug(req.title)
    roles = sorted(set(req.allowed_roles))
    with _lock:
        if doc_id in _register or _col.get(where={"doc_id": doc_id}, limit=1)["ids"]:
            raise HTTPException(409, f"a document called {doc_id} already exists")
        try:
            uploads.preview(paras)  # same size and emptiness checks
        except ValueError as e:
            raise HTTPException(422, str(e))
        ids = uploads.add_to_index(_col, doc_id, req.title, paras, roles)
        _uploads[doc_id] = req.title
        verifier = _orch["B"].verifier
        verifier.doc_texts[doc_id] = "\n\n".join(paras)
        if req.add_to_register:
            # The register is the verifier's own list, separate from the vector-DB tags; leaving
            # the document out of it shows the verifier failing closed.
            verifier.register[doc_id] = set(roles)
            _register[doc_id] = set(roles)
    return {"doc_id": doc_id, "chunks": len(ids), "allowed_roles": roles, "in_register": req.add_to_register}


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str, authorization: str = Header(default="")):
    _staff(authorization)
    if doc_id not in _uploads:
        raise HTTPException(404, "only documents uploaded from the web page can be removed")
    with _lock:
        _col.delete(where={"doc_id": doc_id})
        _uploads.pop(doc_id)
        _orch["B"].verifier.register.pop(doc_id, None)
        _orch["B"].verifier.doc_texts.pop(doc_id, None)
        _register.pop(doc_id, None)
    return {"deleted": doc_id}
