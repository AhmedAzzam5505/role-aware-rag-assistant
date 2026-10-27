"""Writes one JSON line per query: latency, tokens, cost and the verifier's decision."""
import json
import time

from . import config


def log_query(record, path=None):
    path = path or config.LOG_DIR / "queries.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **record}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
