"""Shared settings. Values can be overridden with environment variables."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "data" / "docs"
REAL_DOCS_DIR = ROOT / "data" / "real" / "docs"

# Which documents to index:
#   mock  the 13 documents written by the group (default; all results up to run 5)
#   real  16 public policy documents from four universities (python -m src.fetch_real)
#         + the 7 mock staff/admin documents, because real restricted documents are not public
CORPUS = os.getenv("RAG_CORPUS", "mock")
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", ROOT / ".chroma"))
LOG_DIR = Path(os.getenv("LOG_DIR", ROOT / "logs"))
COLLECTION = os.getenv("COLLECTION", "uni_docs")

ROLES = ("student", "lecturer", "admin")


# Datasets a user can pick in the web page: whose documents answers are built from.
UNIVERSITIES = {
    "uow": ("University of Wollongong", "Australia"),
    "uowd": ("University of Wollongong in Dubai", "UAE"),
    "hw": ("Heriot-Watt University", "UK"),
    "unsw": ("UNSW Sydney", "Australia"),
    "mock": ("Mock University (written by the group)", "mock data"),
    "upload": ("Uploaded documents", "added from the web page"),
}


def university_of(doc_id, corpus=None):
    """Which dataset a document belongs to. In the real corpus the mock staff/admin documents count as
    UOW Dubai internal documents (CSIT305 is a UOWD subject and the salary bands are in AED)."""
    if (corpus or CORPUS) == "mock":
        return "mock"
    for prefix in ("uowd", "uow", "hw", "unsw"):
        if doc_id.startswith(prefix + "_"):
            return prefix
    return "uowd" if doc_id.startswith(("staff_", "admin_")) else "mock"


def corpus_files(corpus=None):
    corpus = corpus or CORPUS
    mock = sorted(DOCS_DIR.glob("*.md"))
    if corpus == "mock":
        return mock
    if corpus == "real":
        real = sorted(REAL_DOCS_DIR.glob("*.md"))
        if not real:
            raise FileNotFoundError("real corpus not built: run `python -m src.fetch_real` first")
        return real + [p for p in mock if not p.stem.startswith("pub_")]
    raise ValueError(f"unknown corpus {corpus!r} (use mock or real)")

# "offline" runs with no API key (local embeddings + extractive answerer + rule-based verifier).
# "openai" uses an OpenAI-compatible API for embeddings, the answerer and the verifier.
MODE = os.getenv("RAG_MODE", "openai" if os.getenv("OPENAI_API_KEY") else "offline")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

TOP_K = int(os.getenv("TOP_K", "4"))
CHUNK_SENTENCES = 2
# Below this similarity the retriever treats the question as not covered by the documents.
MIN_SCORE = float(os.getenv("MIN_SCORE", "0.12"))
# Offline verifier: minimum IDF-weighted share of the question's words the answer must contain.
# Set on the development questions only (v1.1), see src/agents/relevance.py.
REL_MIN_COVERAGE = float(os.getenv("REL_MIN_COVERAGE", "0.25"))

NEUTRAL_REPLY = "I can't help with that. Please contact Student Central for more information."

# Approximate prices (USD per 1M tokens) used to estimate cost in the logs.
PRICE_IN = 0.15
PRICE_OUT = 0.60
