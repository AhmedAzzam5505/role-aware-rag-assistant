# Run 10 notes (16 Nov 2026): INVALID - the new documents were missing from the access register

`python -m eval.run_eval --corpus dubai --out results/run10`. Kept as evidence of a setup bug; do not
use these figures.

The 15 documents added in v1.6 were not added to `data/real/access_register.csv` (it had been generated
once from the 16 v1 documents). Two effects:

- Version B treated every new document as restricted (a document missing from the register fails
  closed), so it refused almost every answer from them: over-refusal 84.6%, accuracy 11.5%.
- The evaluation's ground truth (the same register) counted Version A's citations of new public
  documents as leaks: leak rate 66.7% with normal tagging, which is impossible for public documents.

Fail-closed behaved exactly as designed; the configuration was wrong. Fixed by generating the
register entries for all manifest documents and adding a test that every manifest document is in the
register. The corrected run on the same frozen question set is run 11.
