# Run 7 notes (16 Nov 2026): real corpus, label-form sensitivity markers (v1.2)

`python -m eval.run_eval --corpus real --out results/run7`, offline mode, same corpus, index settings
and 45 real questions as the re-run of run 6. Unit tests: 41 of 41 passed.

## The one change since run 6

Access labels ("STAFF ONLY", "ADMIN ONLY", "CONFIDENTIAL", "HR CONFIDENTIAL") now count only in
label form, i.e. in upper case. Content phrases ("marking guide", "model answer", "do not share",
"watch list") are matched as before. In the corpus, the upper-case labels occur in the restricted
documents and in none of the 16 real public documents. The rule comes from that inspection of the
documents, not from the question results, but it was made after seeing run 6, so both runs are
reported.

## Results (normal tagging)

| Metric | A | B, run 6 (v1.1) | **B, run 7 (v1.2)** |
|---|---|---|---|
| Accuracy | 78.6% [60.5, 89.8] | 71.4% | **78.6%** [60.5, 89.8] |
| Over-refusal | 0% | 17.9% | **3.6%** (R34, which A answered wrongly) |
| Unanswerable refused | 22.2% | 44.4% | **44.4%** (p = 0.5 vs A) |
| Leaks | 0 | 0 | **0** |

Every question where Version B now differs from Version A is a wrong answer turned into the neutral
reply (R14, R15, R28 restricted questions answered with unrelated public text; R34; R44, R45
unanswerable). Version B lost no correct answer.

Leaks with every restricted document mis-tagged: A 7 of 8, B 0 of 8 (p = 0.016), with or without a
wrong register. The mock-corpus results are unchanged (they still match run 5).

## What the real corpus taught us

1. A rule that worked perfectly on documents we wrote ourselves (any "confidential" = restricted) was
   wrong on real documents. Testing on real text found it in one run.
2. Approximate vector search needs care to be repeatable once the index is large (see run 6 notes).
3. The leak protection and the relevance check carry over to real documents. The offline answerer
   still gets 6 of 28 answerable questions wrong (78.6%): with 1,258 chunks from long policies, the
   extractive answerer often picks a neighbouring clause. That is a limit of the offline mode, not of
   the verifier; the openai-mode run remains the main experiment.
