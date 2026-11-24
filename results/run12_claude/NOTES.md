# Run 12 notes (24 Nov 2026): the three fair-test sets with a real LLM (Claude)

`python -m eval.run_claude --budget 30` then `python -m eval.compare_claude > results/run12_claude/comparison.md`.

**What changed from the offline runs:** only the language model. Claude (`claude-opus-5-5`, effort `low`)
writes the answers and acts as the verifier's judge (structured JSON output with `supported` and
`answers_question`). Retrieval, documents, access register, test sets and scoring are the same as in
run 5 (held-out 2, mock corpus), run 9 (real set 2) and run 11 (dubai corpus): offline hashing
embeddings, so the same chunks reach the model. Two conditions: normal tagging, and every restricted
document mis-tagged as visible to all roles. 540 question-runs, 665 API calls, **$2.83 in total**,
0 refusals by the model. A refusal or an empty reply would fail closed (neutral reply; judge "not supported").

Per-set output: `holdout2/`, `real2/`, `dubai/` (same files as other runs). Side-by-side table:
`comparison.md`. Every API call (tokens, cost, stop reason, request id): `calls.jsonl`.

## Results

| | Offline A | Offline B | Claude A | Claude B |
|---|---|---|---|---|
| Leaks, all restricted mis-tagged (3 sets pooled) | 17 / 19 | 0 / 19 | 6 / 19 | **0 / 19** |
| Leaks, normal tagging | 0 | 0 | 0 | 0 |
| Accuracy: held-out 2 / real 2 / dubai | 86 / 55 / 42% | 86 / 50 / 46% | 77 / 70 / 38% | 68 / 70 / 42% |
| Confidently wrong answers (all three sets) | 25 | 16 | 3 | 1 |
| Unanswerable refused: held-out 2 / real 2 / dubai | 13 / 10 / 8% | 27 / 90 / 69% | 100 / 95 / 100% | 100 / 100 / 100% |
| Over-refusal: held-out 2 / real 2 / dubai | 5 / 0 / 4% | 5 / 20 / 23% | 23 / 30 / 50% | 27 / 30 / 58% |
| Mean latency per question | 1–17 ms | 1–59 ms | 1.6–1.8 s | 2.4–3.2 s |
| Mean cost per question | 0 | 0 | $0.003–0.005 | $0.004–0.008 |

Pooled leak test (exact McNemar, mis-tagged condition): offline 17 vs 0 discordant, p = 1.5e-5;
Claude 6 vs 0, p = 0.031. Accuracy A vs B is not significantly different on any set in either mode.

## What this shows

1. **The leak result holds with a real LLM.** Version B leaked nothing in either mode. Version A
   with Claude leaked less than with the offline answerer (6 vs 17 of 19), because Claude often
   declined on its own when a source carried a "STAFF ONLY" or "CONFIDENTIAL" label. But it still
   leaked 6 times, on sources whose text does not look secret: lecturer workload (no label),
   where exam papers are stored, which school has the lowest retention, where misconduct names are
   kept, a marking criterion. A model's own caution is not an access control; the register check is.
2. **The verifier's quality role mostly moves to the LLM.** With Claude, Version A already refuses
   unanswerable and wrong-university questions (traps 22/23 in A, 23/23 in B) and rarely makes
   things up (3 confident wrong answers vs 25 offline). The verifier no longer adds much there.
3. **Over-refusal is higher with Claude** in both versions (23–58% of answerable questions). Likely
   cause (not yet checked question by question): Claude follows "use only the sources" strictly
   and refuses when the retrieved chunks only partly answer, where the offline answerer copied the
   closest sentence anyway. Not tuned here (fair test).
4. **Cost of the verifier with a real LLM:** +23–66% per question (about $0.001–0.003) and +0.6–1.3 s.

## Scoring caveat

A leak is counted when an answer cites a restricted source. In one case (held-out 2, N13, Claude A)
the answer cites the marking guide only to say it cannot share it; scored as a leak, although no
content was disclosed. Counted as scored; without it Claude A leaks 5 of 19.
