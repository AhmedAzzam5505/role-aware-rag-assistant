"""Run 12: the three fair-test sets through Version A and B with Claude as answerer and judge.

Retrieval is unchanged (offline hashing embeddings), so only the LLM part differs from the offline
runs 5, 9 and 11. Needs Anthropic credentials (`ant auth login` or ANTHROPIC_API_KEY) and
`pip install anthropic`. Phases: smoke (6 questions, cost estimate) -> full run, with a hard budget cap.

    python -m eval.run_claude --budget 30 --out results/run12_claude
"""
import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

os.environ["RAG_MODE"] = "offline"  # hashing embeddings; the LLM is injected below
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import anthropic  # noqa: E402

from src import config  # noqa: E402
from src.orchestrator import Orchestrator  # noqa: E402
import eval.run_eval as run_eval  # noqa: E402
from eval.claude_llm import ClaudeLLM, BudgetExceeded, MODEL, EFFORT  # noqa: E402

PLAN = [("holdout2", "mock", "run5"), ("real2", "real", "run9"), ("dubai", "dubai", "run11")]
CONDITIONS = ("normal", "mistagged_all")


def wait_for_credentials(max_wait_s):
    t0 = time.time()
    while True:
        try:
            anthropic.Anthropic().models.retrieve(MODEL)
            print("credentials OK", flush=True)
            return
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as e:
            raise SystemExit(f"credentials rejected: {e}")
        except Exception as e:  # no credentials configured yet
            if time.time() - t0 >= max_wait_s:
                raise SystemExit(f"no credentials after {max_wait_s}s: {type(e).__name__}: {e}")
            time.sleep(15)


def smoke(llm):
    """Six questions on the dubai corpus, A and B, normal tagging; prints answers and cost."""
    config.CORPUS = "dubai"
    col = run_eval.build_index("normal", config.ROOT / ".chroma_eval" / "dubai")
    qs = list(csv.DictReader(open(REPO / "eval" / "test_set_dubai.csv", encoding="utf-8")))
    pick = [q for t in ("answerable", "unanswerable", "restricted") for q in [x for x in qs if x["type"] == t][:2]]
    before = llm.spent
    for version in ("A", "B"):
        o = Orchestrator(col, use_verifier=(version == "B"), llm=llm, log=False)
        for q in pick:
            r = o.ask(q["question"], q["role"])
            print(f"[{version}] {q['id']} {q['type']:12s} {r['verifier_decision']:8s} {r['latency_s']:.1f}s "
                  f"${r['cost_usd']:.4f} | {r['answer'][:110]!r}", flush=True)
    per_q = (llm.spent - before) / (2 * len(pick))
    print(f"smoke: {llm.calls} calls, ${llm.spent - before:.3f}, ~${per_q:.4f} per question-version", flush=True)
    return per_q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=30.0)
    ap.add_argument("--wait", type=int, default=0, help="seconds to wait for credentials")
    ap.add_argument("--out", type=Path, default=REPO / "results" / "run12_claude")
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    wait_for_credentials(args.wait)
    llm = ClaudeLLM(config.NEUTRAL_REPLY, args.budget, out / "calls.jsonl")
    print(f"model={MODEL} effort={EFFORT} budget=${args.budget}", flush=True)

    per_q = smoke(llm)
    n_runs = sum(45 for _ in PLAN) * len(CONDITIONS) * 2
    est = per_q * n_runs
    print(f"estimated full run: {n_runs} question-runs, ~${est:.2f}", flush=True)
    if est > args.budget - llm.spent:
        raise SystemExit(f"estimate ${est:.2f} exceeds remaining budget ${args.budget - llm.spent:.2f}; stopping")

    # Inject Claude into the evaluation harness; keep two tagging conditions.
    run_eval.CONDITIONS = CONDITIONS
    run_eval.make_orchestrator = lambda col, version, condition: Orchestrator(
        col, use_verifier=(version == "B"), llm=llm, log=False)

    for set_name, corpus, ref in PLAN:
        config.CORPUS = corpus
        t0 = time.time()
        print(f"\n=== {set_name} on {corpus} (offline reference: results/{ref})", flush=True)
        try:
            run_eval.run([set_name], out / set_name)
        except BudgetExceeded as e:
            print(f"STOPPED: {e}", flush=True)
            break
        print(f"{set_name} done in {(time.time() - t0) / 60:.1f} min, spent so far ${llm.spent:.2f}", flush=True)

    (out / "run_info.json").write_text(json.dumps({
        "model": MODEL, "effort": EFFORT, "conditions": CONDITIONS, "sets": [p[0] for p in PLAN],
        "calls": llm.calls, "refusals": llm.refusals, "spent_usd": round(llm.spent, 4),
        "finished": time.strftime("%Y-%m-%d %H:%M")}, indent=2))
    print(f"\nALL DONE: {llm.calls} calls, {llm.refusals} refusals, ${llm.spent:.2f}", flush=True)


if __name__ == "__main__":
    main()
