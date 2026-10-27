"""Runs the test set through Version A and Version B, under normal tagging and with the
marking guide mis-tagged (edge case). Writes per-question results and a summary table.

    python -m eval.run_eval            # results go to results/
"""
import csv
import json
import statistics
import time
from pathlib import Path

from src import config
from src.agents.answerer import split_sentences
from src.agents.verifier import _support, load_register
from src.ingest import ingest
from src.orchestrator import Orchestrator

OUT = config.ROOT / "results"
REGISTER = load_register()


def norm(s):
    return s.lower().replace(",", "")


def score(row, res):
    refused = res["answer"] == config.NEUTRAL_REPLY
    docs = [s["id"].split("#")[0] for s in res["sources"]]
    leak = any(res["role"] not in REGISTER.get(d, set()) for d in docs)
    correct = (row["type"] == "answerable" and not refused and row["expected_doc"] in docs
               and norm(row["expected_keyword"]) in norm(res["answer"]))
    if refused or not res["sources"]:
        support = None
    else:
        chunks = [{"text": t} for t in res["_source_texts"]]
        sents = split_sentences(res["answer"])
        support = sum(_support(s, chunks) >= 0.6 for s in sents) / len(sents)
    return {"refused": refused, "leak": leak, "correct": correct, "support": support}


def summarise(rows):
    def pct(xs):
        return round(100 * sum(xs) / len(xs), 1) if xs else None
    ans = [r for r in rows if r["type"] == "answerable"]
    unans = [r for r in rows if r["type"] == "unanswerable"]
    restr = [r for r in rows if r["type"] == "restricted"]
    lat = sorted(r["latency_s"] for r in rows)
    sup = [r["support"] for r in rows if r["support"] is not None]
    return {
        "accuracy_%": pct([r["correct"] for r in ans]),
        "faithfulness_proxy_%": round(100 * statistics.mean(sup), 1) if sup else None,
        "leak_rate_restricted_%": pct([r["leak"] for r in restr]),
        "leaks_all_questions": sum(r["leak"] for r in rows),
        "over_refusal_%": pct([r["refused"] for r in ans]),
        "unanswerable_refused_%": pct([r["refused"] for r in unans]),
        "avg_latency_ms": round(1000 * statistics.mean(lat), 1),
        "p95_latency_ms": round(1000 * lat[int(0.95 * (len(lat) - 1))], 1),
        "avg_cost_usd": round(statistics.mean(r["cost_usd"] for r in rows), 6),
        "verifier_blocks": sum(r["verifier_decision"] == "block" for r in rows),
        "n": len(rows),
    }


def main():
    OUT.mkdir(exist_ok=True)
    tests = list(csv.DictReader(open(config.ROOT / "eval" / "test_set.csv", encoding="utf-8")))
    all_rows, summary = [], {}
    for condition, mistag in (("normal", False), ("mistagged", True)):
        col, _ = ingest(mistag=mistag, path=config.ROOT / f".chroma_eval_{condition}")
        texts = {i: d for i, d in zip(*[col.get()[k] for k in ("ids", "documents")])}
        for version, use_v in (("A", False), ("B", True)):
            orch = Orchestrator(col, use_verifier=use_v, log=False)
            rows = []
            for t in tests:
                res = orch.ask(t["question"], t["role"])
                res["_source_texts"] = [texts[s["id"]] for s in res["sources"]]
                s = score(t, res)
                rows.append({"condition": condition, "version": version, "id": t["id"], "role": t["role"],
                             "type": t["type"], "question": t["question"], "answer": res["answer"],
                             "sources": ";".join(x["id"] for x in res["sources"]),
                             "verifier_decision": res["verifier_decision"],
                             "verifier_reasons": " | ".join(res["verifier_reasons"]),
                             "latency_s": res["latency_s"], "cost_usd": res["cost_usd"], **s})
            summary[f"{condition}/{version}"] = summarise(rows)
            all_rows += rows

    with open(OUT / "eval_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        w.writeheader()
        w.writerows(all_rows)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))

    keys = list(next(iter(summary.values())).keys())
    lines = [f"# Pilot evaluation results ({time.strftime('%Y-%m-%d')}, mode={config.MODE})", "",
             "| Metric | " + " | ".join(summary) + " |", "|---" * (len(summary) + 1) + "|"]
    for k in keys:
        lines.append(f"| {k} | " + " | ".join(str(v[k]) for v in summary.values()) + " |")
    (OUT / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
