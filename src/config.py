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
#   dubai the real corpus + 15 documents from 7 more universities with Dubai campuses (v1.6). Each
#         university is shown under its Dubai campus (UOW Australia policies count as UOW Dubai,
#         main-campus policies of Middlesex, Birmingham, Murdoch, Curtin as their Dubai campuses);
#         UNSW stays as a university without a Dubai campus
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
    "mdx": ("Middlesex University Dubai", "UAE"),
    "uob": ("University of Birmingham Dubai", "UAE"),
    "murdoch": ("Murdoch University Dubai", "UAE"),
    "curtin": ("Curtin University Dubai", "UAE"),
    "amity": ("Amity University Dubai", "UAE"),
    "cud": ("Canadian University Dubai", "UAE"),
    "aud": ("American University in Dubai", "UAE"),
    "mock": ("Mock University (written by the group)", "mock data"),
    "upload": ("Uploaded documents", "added from the web page"),
}
# In the dubai corpus the multi-campus universities are presented under their Dubai campus.
DUBAI_NAMES = {"hw": ("Heriot-Watt University Dubai", "UAE")}
DUBAI_NOTES = {
    "uowd": "UOW Dubai policies + UOW (Australia) main-campus policies",
    "hw": "Dubai campus handbook + Heriot-Watt main-campus policies",
    "mdx": "Middlesex University regulations that apply to the Dubai campus",
    "uob": "University of Birmingham guidance that applies to the Dubai campus",
    "murdoch": "Dubai attendance policy + Murdoch policies for transnational campuses",
    "curtin": "Curtin's assessment manual, which covers its global campuses",
    "unsw": "No Dubai campus: included as a general reference university",
}
REAL_PREFIXES = ("uowd", "uow", "hw", "unsw", "mdx", "uob", "murdoch", "curtin", "amity", "cud", "aud")


def university_label(uid, corpus=None):
    """(name, country) of a dataset, using the Dubai-campus name in the dubai corpus."""
    if (corpus or CORPUS) == "dubai" and uid in DUBAI_NAMES:
        return DUBAI_NAMES[uid]
    return UNIVERSITIES[uid]


def canonical_university(uid, corpus=None):
    """In the dubai corpus UOW Australia is merged into UOW Dubai."""
    return "uowd" if uid == "uow" and (corpus or CORPUS) == "dubai" else uid


def university_of(doc_id, corpus=None):
    """Which dataset a document belongs to. In the real corpus the mock staff/admin documents count as
    UOW Dubai internal documents (CSIT305 is a UOWD subject and the salary bands are in AED)."""
    corpus = corpus or CORPUS
    if corpus == "mock":
        return "mock"
    for prefix in REAL_PREFIXES:
        if doc_id.startswith(prefix + "_"):
            return canonical_university(prefix, corpus)
    return "uowd" if doc_id.startswith(("staff_", "admin_")) else "mock"


# Ways a question can name a university. UOW Dubai is matched (and removed) before UOW, so
# "UOW Dubai" does not also count as the University of Wollongong in Australia.
UNIVERSITY_NAMES = [
    ("uowd", [r"\buowd\b", r"\buow\s+dubai\b", r"\buow\s+in\s+dubai\b", r"\buniversity\s+of\s+wollongong\s+in\s+dubai\b",
              r"\bwollongong\s+in\s+dubai\b"]),
    ("uow", [r"\buow\b", r"\buniversity\s+of\s+wollongong\b", r"\bwollongong\b"]),
    ("hw", [r"\bheriot[\s-]*watt\b", r"\bhwu\b"]),
    ("unsw", [r"\bunsw\b", r"\buniversity\s+of\s+new\s+south\s+wales\b"]),
    ("mdx", [r"\bmiddlesex\b", r"\bmdx\b"]),
    ("uob", [r"\buniversity\s+of\s+birmingham\b", r"\bbirmingham\b", r"\buob\b"]),
    ("murdoch", [r"\bmurdoch\b"]),
    ("curtin", [r"\bcurtin\b"]),
    ("amity", [r"\bamity\b"]),
    ("cud", [r"\bcanadian\s+university(\s+(of\s+)?dubai)?\b", r"\bcud\b"]),
    ("aud", [r"\bamerican\s+university\s+in\s+dubai\b", r"(?<!\d\s)(?<!\d)\baud\b(?!\s*\d)"]),
]


def universities_named(text):
    """Set of university ids named in a question (empty if none)."""
    import re
    text, found = text.lower(), set()
    for uid, patterns in UNIVERSITY_NAMES:
        for pat in patterns:
            if re.search(pat, text):
                found.add(uid)
                text = re.sub(pat, " ", text)
    return found


def corpus_files(corpus=None):
    corpus = corpus or CORPUS
    mock = sorted(DOCS_DIR.glob("*.md"))
    if corpus == "mock":
        return mock
    if corpus == "real":
        real = real_files({"v1"})
        if not real:
            raise FileNotFoundError("real corpus not built: run `python -m src.fetch_real` first")
        return real + [p for p in mock if not p.stem.startswith("pub_")]
    if corpus == "dubai":
        real = real_files({"v1", "v2"})
        if not real:
            raise FileNotFoundError("dubai corpus not built: run `python -m src.fetch_real` first")
        return real + [p for p in mock if not p.stem.startswith("pub_")]
    raise ValueError(f"unknown corpus {corpus!r} (use mock, real or dubai)")


def real_files(sets):
    """Fetched documents of the given manifest sets ('v1' = the 16 of runs 6-9, 'v2' = v1.6 additions)."""
    import csv
    manifest = ROOT / "data" / "real" / "manifest.csv"
    if not manifest.exists():
        return []
    with open(manifest, newline="", encoding="utf-8") as f:
        ids = [r["doc_id"] for r in csv.DictReader(f) if r.get("set", "v1") in sets]
    return [REAL_DOCS_DIR / f"{d}.md" for d in ids if (REAL_DOCS_DIR / f"{d}.md").exists()]

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
