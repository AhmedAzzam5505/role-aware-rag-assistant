"""Mis-tag stress test: how many tagging errors can each configuration tolerate?

Every subset of the restricted documents (2^7 = 128) is mis-tagged as visible to all roles, one
subset at a time, by updating the chunk metadata of one base index. For each subset the questions
run through three configurations:
    A         role filter only
    B         role filter + verifier with the correct access register
    B_labels  role filter + verifier whose register is wrong for the SAME documents (one person
              made both mistakes), so only the sensitivity labels inside the documents remain
Per-subset results are written to subsets.jsonl. The expected value of any metric at a per-document
error rate p is then exact:  E[m] = sum_S p^|S| (1-p)^(n-|S|) m(S)   (see curves.py).

    python -m eval.mistag_stress --smoke     # 3 subsets
    python -m eval.mistag_stress             # all 128 subsets (about 25 min, offline)
    python -m eval.stress_curves             # expected metrics per error rate
"""
import argparse
import csv
import itertools
import json
import os
import sys
import time
from pathlib import Path

os.environ["RAG_CORPUS"] = "dubai"
os.environ["RAG_MODE"] = "offline"
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src import config  # noqa: E402
from src.ingest import ingest  # noqa: E402
from src.orchestrator import Orchestrator  # noqa: E402
from eval.run_eval import REGISTER, RESTRICTED_DOCS, TEST_SETS, score  # noqa: E402

OUT = REPO / "results" / "stress_mistag"


def load_questions():
    """Dubai set in full, plus the restricted questions of the other five sets (deduplicated)."""
    qs, seen = [], set()
    for name in ["dubai", "tuning", "holdout", "holdout2", "real", "real2"]:
        for r in csv.DictReader(open(REPO / "eval" / TEST_SETS[name], encoding="utf-8")):
            if name != "dubai" and r["type"] != "restricted":
                continue
            key = (r["question"].strip().lower(), r["role"])
            if key in seen:
                continue
            seen.add(key)
            qs.append({**r, "qid": f"{name}:{r['id']}", "set": name})
    return qs


def set_mistag(col, base_md, by_doc, docs):
    """Make `docs` visible to every role; every other restricted document gets its true tags."""
    ids, mds = [], []
    for d, cids in by_doc.items():
        for cid in cids:
            md = dict(base_md[cid])
            if d in docs:
                md["allowed_roles"] = ",".join(config.ROLES)
                for r in config.ROLES:
                    md[f"role_{r}"] = True
            ids.append(cid)
            mds.append(md)
    col.update(ids=ids, metadatas=mds)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)

    t0 = time.time()
    col, n = ingest(mistag=False, path=REPO / ".chroma_eval" / "stress")
    got = col.get(include=["documents", "metadatas"])
    texts = dict(zip(got["ids"], got["documents"]))
    base_md = dict(zip(got["ids"], got["metadatas"]))
    restricted = sorted(RESTRICTED_DOCS)
    by_doc = {d: [cid for cid, md in base_md.items() if md["doc_id"] == d] for d in restricted}
    print(f"index: {n} chunks, built in {time.time() - t0:.0f}s; restricted docs: {restricted}", flush=True)
    assert all(by_doc.values()), "a restricted document has no chunks in the dubai index"

    qs = load_questions()
    print(f"questions: {len(qs)} ({sum(q['type'] == 'restricted' for q in qs)} restricted)", flush=True)

    orch = {"A": Orchestrator(col, use_verifier=False, log=False),
            "B": Orchestrator(col, use_verifier=True, log=False),
            "B_labels": Orchestrator(col, use_verifier=True, log=False)}

    if args.smoke:
        subsets = [(), ("staff_csit305_marking_guide",), tuple(restricted)]
    else:
        subsets = [s for k in range(len(restricted) + 1) for s in itertools.combinations(restricted, k)]

    out_path = OUT / ("smoke.jsonl" if args.smoke else "subsets.jsonl")  # gzip it afterwards to commit
    done = set()
    if out_path.exists() and not args.smoke:  # resume
        done = {tuple(json.loads(l)["subset"]) for l in out_path.open()}
    mode = "a" if done else "w"
    with out_path.open(mode) as f:
        for i, s in enumerate(subsets):
            if s in done:
                continue
            ts = time.time()
            set_mistag(col, base_md, by_doc, set(s))
            # B_labels: the register is wrong for exactly the mis-tagged documents.
            orch["B_labels"].verifier.register = {d: (set(config.ROLES) if d in s else roles)
                                                  for d, roles in REGISTER.items()}
            per_q = {}
            for cfg, o in orch.items():
                rows = []
                for q in qs:
                    res = o.ask(q["question"], q["role"])
                    res["_source_texts"] = [texts[x["id"]] for x in res["sources"]]
                    sc = score(q, res)
                    rows.append({"qid": q["qid"], "type": q["type"], "set": q["set"], **sc,
                                 "decision": res["verifier_decision"], "latency_s": res["latency_s"]})
                per_q[cfg] = rows
            f.write(json.dumps({"subset": list(s), "k": len(s), "results": per_q}) + "\n")
            f.flush()
            print(f"[{i + 1}/{len(subsets)}] k={len(s)} {time.time() - ts:.1f}s", flush=True)
    set_mistag(col, base_md, by_doc, set())
    print(f"done in {(time.time() - t0) / 60:.1f} min -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
