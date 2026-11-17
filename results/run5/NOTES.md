# Run 5 notes (16 Nov 2026): verifier v1.1 on a second, frozen held-out set

Run by Nikita Dvornitsyn (`python -m eval.run_eval --out results/run5`), offline mode, Python 3.12,
packages exactly as in `requirements.txt`. Unit tests: 37 of 37 passed (`unit_tests.txt`).

## What changed since run 4

| Change | Commit |
|---|---|
| Second held-out set (45 questions, 22 / 15 / 8), committed **before** any verifier change | `26a3e44` |
| Verifier checks every chunk the answerer saw for leaks, not only cited ones | `1cfdc32` |
| Verifier relevance check (answer type + IDF coverage offline; `answers_question` in the LLM judge); leak removal no longer uses up the quality rewrite | `e99915c` |
| Paired McNemar test for refusals of unanswerable questions | this run |

The relevance rules were set on the pilot set and the first held-out set, which are therefore
development sets from now on. The second held-out set was run once, after the rules were frozen.

## Results

| Version B vs A, normal tagging | Pilot (dev) | Held-out 1 (dev) | **Held-out 2 (fair test)** |
|---|---|---|---|
| Accuracy | 92.6% vs 92.6% | 84.0% vs 76.0% | **86.4% vs 86.4%** |
| Unanswerable refused | 100% vs 100% | 66.7% vs 55.6% | **26.7% vs 13.3%** (2 more of 15, p = 0.5) |
| Over-refusal | 0% vs 0% | 12.0% vs 8.0% | **4.5% vs 4.5%** |

Leak results are the same pattern as run 4 on all three sets: Version B never leaks when only the
vector-DB tag is wrong, and the only Version B leak is the unlabelled `staff_lecturer_workload`
document when the register is wrong too (N15). With every restricted document mis-tagged the A vs B
difference is significant on held-out 2 as well (8 vs 0, p = 0.0078).

## What this means

1. **The leak protection generalises.** Three question sets, four conditions, zero leaks added by B.
2. **The offline relevance check helps a little and costs nothing**, but it does not generalise
   the way the development numbers suggested (+11 points there, +13 points here on a harder set, not
   significant). Held-out 2 was written with many near-miss unanswerable questions, and Version A
   answered 13 of 15 of them with a related sentence. Version B now refuses N08 (a "how many"
   question answered without a number) and N10 (low coverage); the rest still pass because the copied
   sentence shares the question's topic and contains the expected kind of value (N22 "how many exam
   papers" -> "four weeks"; N41 "how many staff at level C" -> "AED 35,000").
3. **Relevance needs language understanding.** Word rules cannot tell "Head of School confirms
   allocations" from "who is the Head of School". The LLM judge in openai mode now asks this
   question directly; measuring it is the main remaining experiment.
4. **Answer accuracy is limited by the offline answerer**, not the verifier: N01, N02, N38 pick a
   neighbouring sentence. Version B does not make these worse.

Checked after the run: N45 ("How many students failed ...") looked like a missed type check, but the
full answer has a second sentence with "four weeks", so the rule behaved as designed. Nothing was
changed after seeing these results.
