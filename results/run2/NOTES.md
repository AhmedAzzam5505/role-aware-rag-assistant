# Run 2 notes (after v0.5 changes)

Changes since run 1: the answerer ignores generic words ("student", "staff", ...), skips lines that
only contain a sensitivity label, needs a stronger match before answering, and the stemmer now
handles "enrolled/enrolments" and "extend/extension"-style endings better.

Results:
- Unanswerable questions now all get the neutral reply (66.7% -> 100%).
- Accuracy 96.3% -> 92.6%. Two answerable questions are still wrong in every version:
  L08 (picks the sentence about breaches instead of "only where the subject outline allows it")
  and A07 (picks "up to seven days" instead of "Head of School").
- An intermediate setting (match threshold 0.45) refused 2 answerable questions (7.4%), so we lowered it to 0.35.
- Mis-tagged edge case unchanged: Version A leaks the marking guide on 2 of 9 restricted questions
  (22.2%); Version B blocks both (0%).
- Over-refusal is 0% for both versions, so on this pilot set the verifier added protection without
  extra refusals.

Caution: the thresholds were tuned on this same pilot set, so these numbers are optimistic. The full
90-question set in Week 7 must include new questions that were not used for tuning.
