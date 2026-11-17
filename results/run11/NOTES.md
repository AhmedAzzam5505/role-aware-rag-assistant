# Run 11 notes (16 Nov 2026): first valid run on the dubai corpus

`python -m eval.run_eval --corpus dubai --out results/run11`, offline mode. Corpus: 31 public documents
from 11 universities (7 Dubai campuses added in v1.6, campuses merged under Dubai) + 7 mock restricted
documents, 4,217 chunks. Question set `eval/test_set_dubai.csv` (pushed in `a622f5b` before any run).
No code or parameter was changed for this corpus; run 10 was invalid (missing register entries).

## Results (normal tagging)

| Metric | Version A | Version B |
|---|---|---|
| Accuracy (26 answerable) | 42.3% [25.5, 61.1] | 46.2% [28.8, 64.5] |
| Wrong-university traps refused (T01–T08) | 1 / 8 | 7 / 8 |
| Unanswerable anywhere refused (G01–G05) | 0 / 5 | 2 / 5 |
| All unanswerable refused | 7.7% | 69.2% (8 vs 0 discordant, p = 0.0078) |
| Over-refusal | 3.8% | 23.1% (6 of 26) |
| Leaks, normal tagging | 0 | 0 |
| Leaks, all restricted documents mis-tagged | 5 / 6 | 0 / 6 (p = 0.0625) |

The wrong-university check carries over to the larger corpus: it rejected the Heriot-Watt Dubai
source for a Middlesex question (D06) and the rewrite found the right Middlesex rule.

## Problem found: a content phrase in a real public document

`curtin_assessment_manual` mentions "marking guide" once, as an ordinary term. Students may not see
documents containing that phrase (it is one of the verifier's content markers), and the marker check
reads the whole source document, so every Curtin chunk counts as restricted for a student. Version B
dropped Curtin sources on 11 of 45 questions and lost one correct answer (D02). This is the same
weakness as "confidential" in run 6, now for a content phrase: rules written for our own mock documents
break on real ones. Not changed here (this set is the fair test for the dubai corpus); a fix needs a new
question set.

## Why accuracy is low for both versions

With 4,217 chunks, a few very long documents (Canadian University Dubai handbook, about 81,000 words;
Middlesex regulations, about 48,000; Curtin manual, about 30,000) fill the top 4 for many questions, and
the offline extractive answerer often picks a neighbouring clause. Retrieval quality, not the verifier,
limits accuracy here; the openai-mode embeddings and answerer are the obvious next experiment.
