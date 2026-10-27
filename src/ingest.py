"""Offline ingestion: read documents, split into chunks, tag each chunk with its allowed roles,
embed and store in ChromaDB.

Usage:
    python -m src.ingest                 # normal tagging
    python -m src.ingest --mistag        # edge case: marking guide wrongly tagged as visible to students
"""
import argparse
import re

from . import config
from .store import get_collection

MISTAG_DOC = "staff_csit305_marking_guide"


def parse_doc(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    meta["allowed_roles"] = [r.strip() for r in meta["allowed_roles"].split(",")]
    meta["doc_id"] = path.stem
    return meta, m.group(2).strip()


def chunk(body, n=config.CHUNK_SENTENCES):
    paras = [p.strip() for p in body.split("\n\n") if p.strip()]
    return [" ".join(paras[i:i + n]) for i in range(0, len(paras), n)]


def build_records(mistag=False):
    records = []
    for path in sorted(config.DOCS_DIR.glob("*.md")):
        meta, body = parse_doc(path)
        roles = list(meta["allowed_roles"])
        if mistag and meta["doc_id"] == MISTAG_DOC:
            roles = list(config.ROLES)  # simulated human error when uploading
        for i, text in enumerate(chunk(body)):
            md = {
                "doc_id": meta["doc_id"],
                "title": meta["title"],
                "sensitivity": meta["sensitivity"],
                "allowed_roles": ",".join(roles),
            }
            for r in config.ROLES:
                md[f"role_{r}"] = r in roles
            records.append((f"{meta['doc_id']}#{i}", text, md))
    return records


def ingest(mistag=False, path=None):
    col = get_collection(path=path, reset=True)
    recs = build_records(mistag)
    col.add(ids=[r[0] for r in recs], documents=[r[1] for r in recs], metadatas=[r[2] for r in recs])
    return col, len(recs)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mistag", action="store_true")
    args = ap.parse_args()
    _, n = ingest(args.mistag)
    print(f"Stored {n} chunks in {config.CHROMA_DIR} (mode={config.MODE}, mistag={args.mistag})")
