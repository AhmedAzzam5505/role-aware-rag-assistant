"""Uploading a document from the web page, and showing how it is chunked and embedded.

Two steps, so the page can teach what happens before a document can be retrieved:

1. preview(): extract the text, split it into chunks exactly as `src.ingest` does, embed every chunk
   and (optionally) score each chunk against a question with the same cosine similarity the
   retriever uses. Nothing is stored.
2. add_to_index(): store the chunks in the live ChromaDB collection with role tags, and (by choice)
   an entry in the verifier's access register. Leaving the register entry out shows the verifier
   failing closed: an unregistered document is treated as restricted.

Uploads live only in the running API process: rebuilding the index (`python -m src.ingest` or the
demo switch) removes them, and they are never part of the evaluation corpus.
"""
import math
import re

from . import config
from .embeddings import HashingEmbedding, get_embedding
from .fetch_real import html_to_paragraphs, pdf_to_paragraphs
from .ingest import chunk

MAX_BYTES = 2_000_000
MAX_CHUNKS = 300
SUPPORTED = (".pdf", ".html", ".htm", ".md", ".txt")


def extract_paragraphs(filename, data: bytes):
    name = filename.lower()
    if not name.endswith(SUPPORTED):
        raise ValueError(f"unsupported file type (use {', '.join(SUPPORTED)})")
    if len(data) > MAX_BYTES:
        raise ValueError(f"file too large (max {MAX_BYTES // 1_000_000} MB)")
    if name.endswith(".pdf"):
        return pdf_to_paragraphs(data)
    text = data.decode("utf-8", errors="replace")
    if name.endswith((".html", ".htm")):
        return html_to_paragraphs(text)
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)  # front matter, if any
    return [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def slug(title):
    return "upload_" + (re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:40] or "document")


def _cosine(a, b):
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return sum(x * y for x, y in zip(a, b)) / (na * nb)


def preview(paragraphs, question=None):
    chunks = chunk("\n\n".join(paragraphs))
    if not chunks:
        raise ValueError("no text found in the file")
    if len(chunks) > MAX_CHUNKS:
        raise ValueError(f"too many chunks ({len(chunks)}, max {MAX_CHUNKS})")
    emb = get_embedding()
    vectors = emb(chunks)
    explain = isinstance(emb, HashingEmbedding)
    out = []
    for i, (text, vec) in enumerate(zip(chunks, vectors)):
        out.append({
            "index": i,
            "text": text,
            "words": len(text.split()),
            "dims": len(vec),
            "nonzero_dims": sum(1 for x in vec if x),
            "vector_head": [round(x, 4) for x in vec[:64]],
            "features": emb.explain(text) if explain else None,
        })
    result = {"paragraphs": len(paragraphs), "chunks": out, "embedding": emb.name(),
              "chunk_rule": f"{config.CHUNK_SENTENCES} paragraphs per chunk",
              "min_score": config.MIN_SCORE, "top_k": config.TOP_K}
    if question:
        q = emb([question])[0]
        result["question_features"] = emb.explain(question) if explain else None
        scores = [round(_cosine(q, v), 3) for v in vectors]
        ranked = sorted(range(len(scores)), key=lambda i: (-scores[i], i))
        for c in out:
            c["score"] = scores[c["index"]]
            c["rank"] = ranked.index(c["index"]) + 1
            c["retrieved"] = c["rank"] <= config.TOP_K and c["score"] >= config.MIN_SCORE
    return result


def add_to_index(col, doc_id, title, paragraphs, roles):
    chunks = chunk("\n\n".join(paragraphs))
    md = {"doc_id": doc_id, "title": title, "sensitivity": "public" if set(roles) == set(config.ROLES)
          else "restricted", "allowed_roles": ",".join(roles)}
    for r in config.ROLES:
        md[f"role_{r}"] = r in roles
    ids = [f"{doc_id}#{i}" for i in range(len(chunks))]
    col.add(ids=ids, documents=chunks, metadatas=[dict(md) for _ in chunks])
    return ids
