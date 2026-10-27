"""Shared settings. Values can be overridden with environment variables."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "data" / "docs"
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", ROOT / ".chroma"))
LOG_DIR = Path(os.getenv("LOG_DIR", ROOT / "logs"))
COLLECTION = os.getenv("COLLECTION", "uni_docs")

ROLES = ("student", "lecturer", "admin")

# "offline" runs with no API key (local embeddings + extractive answerer + rule-based verifier).
# "openai" uses an OpenAI-compatible API for embeddings, the answerer and the verifier.
MODE = os.getenv("RAG_MODE", "openai" if os.getenv("OPENAI_API_KEY") else "offline")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

TOP_K = int(os.getenv("TOP_K", "4"))
CHUNK_SENTENCES = 2
# Below this similarity the retriever treats the question as not covered by the documents.
MIN_SCORE = float(os.getenv("MIN_SCORE", "0.12"))

NEUTRAL_REPLY = "I can't help with that. Please contact Student Central for more information."

# Approximate prices (USD per 1M tokens) used to estimate cost in the logs.
PRICE_IN = 0.15
PRICE_OUT = 0.60
