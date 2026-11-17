# Run 4 notes (16 Nov 2026): held-out test set, all-document mis-tags, confidence intervals

Run by Nikita Dvornitsyn (`python -m eval.run_eval --out results/run4`), offline mode, Python 3.12,
packages exactly as in `requirements.txt`. Unit tests: 32 of 32 passed (`unit_tests.txt`).

## What changed since run 3

| Change | Commit | Effect on the pilot (tuning) set |
|---|---|---|
| Verifier checks labels against the whole source document | `fix(verifier)` | none (it only matters when the register is also wrong) |
| Answerer adds a second sentence only from the same document | `fix(answerer)` | 5 answers lose an unrelated second sentence; metrics identical |
| New unlabelled restricted document `staff_lecturer_workload` | `data:` | none |
| 45 held-out questions (`eval/test_set_holdout.csv`) | `data:` | n/a (new set) |
| Two new conditions: `mistagged_all`, `mistagged_all_bad_register` | `feat(eval)` | n/a |
| 95% Wilson intervals and paired exact McNemar test | `feat(eval)` | n/a |

The pilot set reproduces run 3 exactly (accuracy 92.6%, mis-tagged leak A 22.2% vs B 0%).

## What the held-out set shows

The held-out questions were written after all tuning and **no parameter was changed after
seeing these results**. They are therefore a fairer estimate than the pilot numbers.

| Metric (normal tagging, Version B) | Pilot set | Held-out set |
|---|---|---|
| Accuracy (answerable) | 92.6% [76.6, 97.9] | 76.0% [56.6, 88.5] |
| Unanswerable correctly refused | 100% | 55.6% (5 of 9) |
| Over-refusal | 0% | 8.0% (2 of 25) |

So the offline answerer was over-fitted to the pilot questions. The failures fall into two groups:

1. **Off-topic answers to unanswerable questions (H09, H25, H43, H45).** The answerer copies a
   sentence that shares one word with the question ("Wi-Fi", "room", "annual", "HR committee").
   Version B does **not** catch these: the verifier checks that every sentence is supported by its
   source, and a copied sentence always is. The verifier checks faithfulness, not whether the answer
   is relevant to the question. This is a finding for the paper, not something we fixed here,
   because fixing it now would mean tuning on the held-out set.
2. **Wrong passage chosen (H01, H02, H18, H21) and refusals of answerable questions (H05, H32)**,
   from the bag-of-words matching of the offline mode. The openai mode should be compared on the
   same questions.

## Leak results across conditions

| Condition | Pilot A | Pilot B | Held-out A | Held-out B |
|---|---|---|---|---|
| normal | 0/9 | 0/9 | 0/11 | 0/11 |
| mistagged (marking guide only) | 2/9 | 0/9 | 2/11 | 0/11 |
| mistagged_all | 9/9 | 0/9 | 11/11 | 0/11 |
| mistagged_all_bad_register | 9/9 | 0/9 | 11/11 | **1/11** |

- **Paired test:** with only the marking guide mis-tagged, A and B differ on just 2 questions, so the
  exact McNemar p = 0.5. On its own, the original pilot edge case is **not statistically significant**.
  With every restricted document mis-tagged the difference is significant (p = 0.0039 pilot,
  p = 0.001 held-out). The paper should report the interval, not only "22.2% vs 0%".
- **The one leak in Version B** is H15 from `staff_lecturer_workload`, the document with no
  sensitivity label, when the access register is also wrong. This is the expected limit of the
  design: with both the tag and the register wrong and no label in the text, nothing independent
  is left to catch it. It confirms the register is the main safeguard and the labels are a backup.
- Version B never added a leak (`only B leaked` = 0 everywhere) and blocked nothing on normal tagging.
