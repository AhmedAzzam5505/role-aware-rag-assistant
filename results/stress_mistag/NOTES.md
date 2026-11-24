# Mis-tag stress test (23 Nov 2026): how many tagging errors can each version tolerate?

`python -m eval.mistag_stress` (offline, dubai corpus, about 24 min), then `python -m eval.stress_curves`.
Needs the real documents (`python -m src.fetch_real`). Raw results: `subsets.jsonl.gz` (one line per
subset, per-question results for every configuration); expected values: `curves.json`, `summary.txt`.

**Why.** The main experiment uses two extremes: every tag right, or every restricted tag wrong. Real
tagging errors are in between, so this test asks how leaks grow with the error rate.

**Design.** Every subset of the 7 restricted documents (2^7 = 128) is mis-tagged as visible to all roles,
one subset at a time, by updating the chunk metadata of one dubai index (4,217 chunks). For each subset,
80 questions run through three configurations: the full dubai set plus the restricted questions of the
other five sets, deduplicated (41 restricted, 26 answerable, 13 unanswerable).

| Configuration | What it is |
|---|---|
| A | role filter only |
| B | role filter + verifier with the correct access register |
| B_labels | role filter + verifier whose register is wrong for the same documents (one person made both mistakes), so only the labels inside the documents remain |

If each document is mis-tagged independently with probability p, the expected value of any metric is
exact, with no sampling: `E[m](p) = sum over subsets S of p^|S| (1-p)^(7-|S|) m(S)`.

## Results

| Mis-tag rate per document | 1% | 2% | 5% | 10% | 25% | 50% | 100% |
|---|---|---|---|---|---|---|---|
| Expected share of restricted questions leaked, A | 0.9% | 1.7% | 4.3% | 8.5% | 21.3% | 42.7% | 85.4% |
| Chance of at least one leak, A | 6.8% | 13.2% | 30.2% | 52.2% | 86.7% | 99.2% | 100% |
| B (both measures) | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| Expected share leaked, B_labels | 0.0% | 0.1% | 0.2% | 0.5% | 1.2% | 2.4% | 4.9% |
| Chance of at least one leak, B_labels | 1% | 2% | 5% | 10% | 25% | 50% | 100% |

Accuracy (42.3 / 46.2 / 46.2%), over-refusal (3.8 / 23.1 / 23.1%), unanswerable refused (7.7 / 69.2 /
69.2%) and latency (about 20 / 60 / 60 ms) do not depend on the error rate (A / B / B_labels).

Leak share in A when only one document is mis-tagged: admin_enrolment_report 22.0%,
admin_misconduct_register 19.5%, admin_staff_salary_bands 17.1%, staff_special_consideration_procedure
12.2%, staff_csit305_marking_guide, staff_exam_moderation and staff_lecturer_workload 4.9% each.
B_labels leaks only through `staff_lecturer_workload`, the one restricted document without a label, so its
chance of a leak equals the error rate.

## What this shows

1. A's leaks grow roughly in proportion to the error rate: at 5% per document there is a 30% chance that
   something leaks, at 10% about 50%.
2. B with a correct register leaks nothing at any error rate.
3. If the register is wrong too, labels catch everything except the unlabelled document. Practical rule:
   keep the register correct and put a label in every restricted document.
4. The verifier's costs are paid at every error rate; its protection matters when tags cannot be trusted.

**Limits.** Seven restricted documents, all mock; offline mode only; errors assumed independent per document.
