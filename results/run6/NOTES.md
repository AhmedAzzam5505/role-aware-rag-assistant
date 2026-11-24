# Run 6 notes (16 Nov 2026): first run on the real corpus, verifier v1.1 unchanged

`python -m eval.run_eval --corpus real --out results/run6`, offline mode. Corpus: 16 public policy
documents from UOW, UOW Dubai, Heriot-Watt and UNSW (fetched 16 Nov 2026, hashes in
`data/real/hashes.csv`) + the 7 mock staff/admin documents, 1,258 chunks. Test set:
`eval/test_set_real.csv` (45 questions, committed before this run). **No code or parameter was
changed for the real corpus**: this is the v1.1 system exactly as tuned on the mock documents.

## Results (normal tagging)

| Metric | Version A | Version B |
|---|---|---|
| Accuracy | 78.6% [60.5, 89.8] | 71.4% [52.9, 84.7] |
| Over-refusal | 0% | **17.9%** (5 of 28) |
| Unanswerable refused | 22.2% | 44.4% |
| Leaks | 0 | 0 |

With every restricted document mis-tagged, Version A leaked on 7 of 8 restricted questions and
Version B on none (p = 0.016). With the marking guide alone mis-tagged, neither version leaked: in a
corpus of about 1,260 chunks the guide no longer ranks in the top 4 for these questions.

## Problem found: sensitivity labels give false alarms on real documents

Version B removed correct sources and refused or changed correct answers (R05, R07) because of the
word "confidential". Nine of the 16 real public documents use it in ordinary sentences ("a fair and
confidential process", "confidential advice"). Since v0.11 the verifier looks for labels in the whole
source document, so for a student every chunk of those nine documents counts as restricted.

This did not show up on the mock documents, where "confidential" only appeared as a label written by
the group. It is the limitation listed in `docs/TESTING.md` section 6 ("the wording, including the
STAFF ONLY labels, may make leaks easier to detect than with real documents"), now measured.

The relevance check behaved as intended on real documents: it refused two unanswerable questions that
Version A answered off-topic (R44, R45) and an answerable question that Version A got wrong anyway (R34).

Next: match labels only in label form (upper case, as in "STAFF ONLY", "CONFIDENTIAL"), which occurs
in the restricted documents and in none of the 16 real public ones. Re-run as run 7.

## Re-run with deterministic retrieval (same day)

The first run 6 showed different Version A results for `mistagged_all` and
`mistagged_all_bad_register`, although Version A has no verifier and both conditions use the same
mis-tagging. Cause: ChromaDB's approximate (HNSW) search with its default search beam is not
repeatable on a 1,258-chunk index; rebuilding the index changed the top 4 for 1 of 45 questions.
The 29-chunk mock index was not affected.

Fix (`fix(retriever)`): a wide search beam (`ef_search` 2000) and ties broken by chunk id. Five
rebuilds of the real index now give identical top-4 results for all 90 question/role pairs, and the
mock results still match run 5 exactly. The files in this folder are the re-run, still with the
**v1.1 verifier unchanged**. Normal-tagging figures are the same as in the first run; the
`mistagged_all_bad_register` column changed (Version A leaks 62.5% -> 87.5%, Version B over-refusal
21.4% -> 17.9%), and the two mis-tag columns are now consistent with each other.
