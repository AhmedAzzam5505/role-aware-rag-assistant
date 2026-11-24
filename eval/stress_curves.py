"""Turns out/subsets.jsonl into exact expected metrics at per-document mis-tag rates p.

E[m](p) = sum over subsets S of p^|S| (1-p)^(n-|S|) * m(S),  n = number of restricted documents.
"""
import gzip
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "results" / "stress_mistag"
src = OUT / "subsets.jsonl"
rows = [json.loads(l) for l in (src.open() if src.exists() else gzip.open(OUT / "subsets.jsonl.gz", "rt"))]
N = max(r["k"] for r in rows)
assert len(rows) == 2 ** N, f"expected {2 ** N} subsets, got {len(rows)}"
CFGS = ["A", "B", "B_labels"]


def metrics(res):
    restr = [r for r in res if r["type"] == "restricted"]
    ans = [r for r in res if r["type"] == "answerable"]
    un = [r for r in res if r["type"] == "unanswerable"]
    return {
        "leak_rate": sum(r["leak"] for r in restr) / len(restr),        # share of restricted questions leaked
        "any_leak": float(any(r["leak"] for r in restr)),                 # at least one leak in the set
        "leaks_all": sum(r["leak"] for r in res),                          # leaks on any question type
        "accuracy": sum(r["correct"] for r in ans) / len(ans),
        "over_refusal": sum(r["refused"] for r in ans) / len(ans),
        "unans_refused": sum(r["refused"] for r in un) / len(un),
        "latency_ms": 1000 * sum(r["latency_s"] for r in res) / len(res),
    }


per = [{"subset": r["subset"], "k": r["k"], **{c: metrics(r["results"][c]) for c in CFGS}} for r in rows]


def expected(p, cfg, m):
    return sum(p ** x["k"] * (1 - p) ** (N - x["k"]) * x[cfg][m] for x in per)


RATES = [0, 0.01, 0.02, 0.05, 0.10, 0.25, 0.50, 1.0]
METRICS = ["leak_rate", "any_leak", "accuracy", "over_refusal", "unans_refused", "latency_ms"]
table = {p: {c: {m: expected(p, c, m) for m in METRICS} for c in CFGS} for p in RATES}

# dense curve on a log axis for the chart
dense = [round(10 ** (-2 + 2 * i / 80), 5) for i in range(81)]  # 1% .. 100%
curve = {c: [[p, expected(p, c, "leak_rate")] for p in dense] for c in CFGS}

# which single document drives the leaks of each configuration (k = 1 subsets)
single = {x["subset"][0]: {c: x[c]["leak_rate"] for c in CFGS} for x in per if x["k"] == 1}

n_restr = sum(r["type"] == "restricted" for r in rows[0]["results"]["A"])
n_ans = sum(r["type"] == "answerable" for r in rows[0]["results"]["A"])
(OUT / "curves.json").write_text(json.dumps(
    {"n_docs": N, "n_restricted_q": n_restr, "n_answerable_q": n_ans,
     "table": {str(p): v for p, v in table.items()}, "curve": curve, "single_doc": single}, indent=1))

pct = lambda v: f"{100 * v:.1f}%"
print(f"{N} restricted documents, {n_restr} restricted questions, {n_ans} answerable (dubai set)\n")
print("Expected share of restricted questions that leak, by per-document mis-tag rate")
print("| rate | exp. docs mis-tagged | A | B | B_labels |")
for p in RATES:
    t = table[p]
    print(f"| {pct(p)} | {N * p:.2f} | {pct(t['A']['leak_rate'])} | {pct(t['B']['leak_rate'])} | {pct(t['B_labels']['leak_rate'])} |")
print("\nProbability that at least one restricted question leaks")
for p in RATES:
    t = table[p]
    print(f"| {pct(p)} | {pct(t['A']['any_leak'])} | {pct(t['B']['any_leak'])} | {pct(t['B_labels']['any_leak'])} |")
print("\nAnswer quality on the dubai set (A / B / B_labels)")
for m in ["accuracy", "over_refusal", "unans_refused", "latency_ms"]:
    for p in [0, 0.10, 1.0]:
        t = table[p]
        f = (lambda v: f"{v:.1f}") if m == "latency_ms" else pct
        print(f"  {m:14s} p={pct(p):6s}  " + " / ".join(f(t[c][m]) for c in CFGS))
print("\nLeak share when only ONE document is mis-tagged")
for d, v in sorted(single.items()):
    print(f"  {d:40s} " + "  ".join(f"{c}={pct(v[c])}" for c in CFGS))
