"""Offline (runs 5, 9, 11) vs Claude (run 12) on the three fair-test sets, from per-question CSVs."""
import csv, json, sys
from math import comb
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
CL = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "results" / "run12_claude"
SETS = {"holdout2": "run5", "real2": "run9", "dubai": "run11"}
TRAP = {"real2": "X", "dubai": "T"}
T = lambda v: v == "True"
def mcn(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)
def load(path, s):
    return [r for r in csv.DictReader(open(path, encoding="utf-8")) if r.get("set", s) == s]
def get(R, cond, ver):
    return {r["id"]: r for r in R if r["condition"] == cond and r["version"] == ver}
def stats(R, s):
    out = {}
    for ver in "AB":
        n, m = get(R, "normal", ver), get(R, "mistagged_all", ver)
        ans = [i for i in n if n[i]["type"] == "answerable"]
        un = [i for i in n if n[i]["type"] == "unanswerable"]
        tr = [i for i in un if s in TRAP and i.startswith(TRAP[s])]
        rs = [i for i in m if m[i]["type"] == "restricted"]
        out[ver] = dict(
            acc=(sum(T(n[i]["correct"]) for i in ans), len(ans)),
            overref=(sum(T(n[i]["refused"]) for i in ans), len(ans)),
            unref=(sum(T(n[i]["refused"]) for i in un), len(un)),
            traps=(sum(T(n[i]["refused"]) for i in tr), len(tr)),
            leak_norm=sum(T(r["leak"]) for r in n.values()),
            leak_mis=(sum(T(m[i]["leak"]) for i in rs), len(rs)),
            lat=1000 * sum(float(r["latency_s"]) for r in n.values()) / len(n),
            cost=sum(float(r.get("cost_usd") or 0) for r in n.values()) / len(n),
            wrong=sum(not T(n[i]["correct"]) and not T(n[i]["refused"]) for i in ans),
        )
    n_a, n_b = get(R, "normal", "A"), get(R, "normal", "B")
    ans = [i for i in n_a if n_a[i]["type"] == "answerable"]
    out["acc_p"] = mcn(sum(T(n_a[i]["correct"]) and not T(n_b[i]["correct"]) for i in ans),
                       sum(T(n_b[i]["correct"]) and not T(n_a[i]["correct"]) for i in ans))
    m_a, m_b = get(R, "mistagged_all", "A"), get(R, "mistagged_all", "B")
    rs = [i for i in m_a if m_a[i]["type"] == "restricted"]
    out["leak_bc"] = (sum(T(m_a[i]["leak"]) and not T(m_b[i]["leak"]) for i in rs),
                      sum(T(m_b[i]["leak"]) and not T(m_a[i]["leak"]) for i in rs))
    return out
res = {}
for s, run in SETS.items():
    res[s] = {"offline": stats(load(REPO / "results" / run / "eval_results.csv", s), s),
              "claude": stats(load(CL / s / "eval_results.csv", s), s)}
f = lambda t: f"{t[0]}/{t[1]} ({100*t[0]/t[1]:.0f}%)" if t[1] else "-"
pool = {k: [0, 0] for k in ("offline", "claude")}
for s, d in res.items():
    print(f"\n### {s}")
    print("| metric | offline A | offline B | Claude A | Claude B |\n|---|---|---|---|---|")
    for key, lab in [("acc","accuracy"),("wrong","confident wrong answers"),("overref","over-refusal"),("unref","unanswerable refused"),
                     ("traps","wrong-university traps refused"),("leak_norm","leaks, normal tagging"),("leak_mis","leaks, all restricted mis-tagged"),
                     ("lat","mean latency ms"),("cost","mean cost per question $")]:
        cells = []
        for src in ("offline", "claude"):
            for v in "AB":
                x = d[src][v][key]
                cells.append(f(x) if isinstance(x, tuple) else (f"{x:.4f}" if key=="cost" else (f"{x:.0f}" if key=="lat" else str(x))))
        if key == "traps" and s not in TRAP: continue
        print(f"| {lab} | " + " | ".join(cells) + " |")
    for src in ("offline", "claude"):
        b, c = d[src]["leak_bc"]; pool[src][0] += b; pool[src][1] += c
        print(f"{src}: accuracy A vs B paired p={d[src]['acc_p']:.3f}; leaks only-A {b} only-B {c} p={mcn(b,c):.4f}")
for src, (b, c) in pool.items():
    print(f"POOLED {src}: only A leaked {b}, only B {c}, exact McNemar p={mcn(b,c):.2e}")
json.dump(res, open(CL / "comparison.json", "w"), indent=1)
