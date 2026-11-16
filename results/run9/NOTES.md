# Run 9 notes (16 Nov 2026): university check, tested on the frozen second real question set

`python -m eval.run_eval --corpus real --out results/run9` runs both real sets (`real` = development
set since this change, `real2` = fair test, committed and pushed in `0e570d6` before the change).
Offline mode, same corpus as run 8. Unit tests: 51 of 51 passed.

## The change (v1.5)

The verifier rejects a cited source that comes from a different university than the one the question
names ("At Heriot-Watt, ..." answered from a UOW policy), rewrites once without it, then blocks.

## Results on real set 2 (fair test, normal tagging)

| Metric | Version A | Version B |
|---|---|---|
| "Wrong university" traps refused (X01–X15) | 1 / 15 | **14 / 15** |
| Other unanswerable refused (U01–U05) | 1 / 5 | 4 / 5 |
| All unanswerable refused | 10.0% | **90.0%** (16 vs 0 discordant, exact McNemar p < 0.001) |
| Accuracy (20 answerable) | 55.0% [34.2, 74.2] | 50.0% [29.9, 70.1] |
| Over-refusal | 0% | 20.0% (4 of 20) |
| Leaks, all restricted documents mis-tagged | 4 / 5 | 0 / 5 (p = 0.125) |

Version B fixed one answer (Q05: the UNSW source was rejected and the rewrite found the right
Heriot-Watt rule) and lost two correct ones:

- **Q09** "When must final online assessments be scheduled at Heriot-Watt?" -> "during exam periods":
  the offline "time" rule knows "period" but not "periods". A rule bug found on new questions.
- **Q14** UOW Dubai second-week refund: the answer is a long refund table that covers only 0.24 of the
  question (threshold 0.25).

Q13 and Q18 were wrong in Version A and refused in Version B. Neither rule was changed after this
run, because that would make real set 2 a development set.

Not caught: X04 and U04 were answered with Heriot-Watt website menu text ("• Mitigating Circumstances |
Heriot-Watt University • ..."), so the source is from the right university but the text is page
furniture. Another extraction clean-up for a later corpus version.

On real set 1 (development) the change refused one more unanswerable question (R26) and lost
nothing; accuracy stays 78.6%. Mock results are unchanged (still match run 5).

## Take-away for the paper

On questions that name a university, checking the source's university is the single most effective
verifier rule we have tested: it turned 14 of 15 confidently wrong answers into refusals. The cost on
this set was two lost correct answers, both from the older offline relevance rules, not from the new
check.
