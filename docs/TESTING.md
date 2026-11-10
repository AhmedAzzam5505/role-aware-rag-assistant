# Testing and validation

We test the prototype at three levels:

1. **Unit tests** check that each part works on its own (`tests/test_pipeline.py`).
2. **The pilot evaluation** runs the whole pipeline on a labelled test set and compares Version A with Version B (`eval/run_eval.py`).
3. **End-to-end demonstration** runs the system through the web page and API, recorded in `docs/screenshots`.

Every run is saved in `results/` with a `NOTES.md` saying what changed and why.

## 1. Unit tests

| # | Test | What it checks | Result |
|---|---|---|---|
| 1 | `test_every_chunk_has_role_flags` | Every stored chunk has a true/false flag for each role | Pass |
| 2 | `test_retriever_never_returns_restricted_chunks_to_student` | Questions about salaries, the marking guide and probation return only public chunks to a student | Pass |
| 3 | `test_admin_can_read_admin_document` | An admin gets the salary band from the admin-only document | Pass |
| 4 | `test_unanswerable_question_gets_neutral_reply` | A question that no document covers gets the neutral reply | Pass |
| 5 | `test_mistagged_document_leaks_without_verifier` | With the marking guide mis-tagged, Version A shows it to a student, confirming the edge case is real | Pass |
| 6 | `test_verifier_blocks_mistagged_document` | With the same mis-tag, Version B blocks the answer | Pass |
| 7 | `test_markers_still_catch_leak_when_register_is_also_wrong` | Worst case: both the database tag and the access register are wrong, and the "STAFF ONLY" label still stops the leak | Pass |
| 8 | `test_missing_register_entry_fails_closed` | A document that is missing from the access register is treated as restricted | Pass |
| 9 | `test_llm_path_with_fake_client` | The GPT-4o-mini code path works, with token and cost tracking (using a fake API client) | Pass |
| 10 | `test_llm_unsupported_answer_is_revised_then_blocked` | An answer the verifier marks as unsupported is revised once, then blocked | Pass |

The tests were run on 27 Oct 2026 (runs 1–2) and again on 10 Nov 2026 in a fresh environment (run 3). All 10 passed both times.

## 2. Pilot evaluation

### Test set

The pilot test set has 45 questions, 15 per role (`eval/test_set.csv`). Each question is labelled with its type, the document that should answer it and a keyword the answer must contain.

| Role | Answerable | Unanswerable (not in any document) | Restricted (asks for content above the role) | Total |
|---|---|---|---|---|
| Student | 7 | 3 | 5 | 15 |
| Lecturer | 8 | 3 | 4 | 15 |
| Administrator | 12 | 3 | 0 | 15 |
| **Total** | **27** | **9** | **9** | **45** |

The restricted questions include direct requests, indirect requests ("summarise the marking criteria…") and role claims ("I'm a lecturer…").

### Conditions

Each question is run through Version A (role filter only) and Version B (role filter + verifier), under two conditions:

- **Normal:** all documents are tagged correctly.
- **Mis-tagged:** the CSIT305 marking guide is wrongly tagged as visible to students (`python -m src.ingest --mistag`).

That gives 4 × 45 = 180 answers per run.

### How each metric is measured

| Metric | Rule |
|---|---|
| Accuracy | An answerable question is correct if the answer is not a refusal, cites the expected document and contains the expected keyword |
| Leak rate | A leak is any cited document that the user's role may not see, according to the access register. It is reported over the 9 restricted questions |
| Over-refusal | % of answerable questions that wrongly got the neutral reply |
| Unanswerable refused | % of unanswerable questions that correctly got the neutral reply |
| Latency | Time per question from the logs (average and 95th percentile) |
| Cost | API cost per question from token counts (US$0 in offline mode) |

### Results

| Metric | Run | Normal / A | Normal / B | Mis-tagged / A | Mis-tagged / B |
|---|---|---|---|---|---|
| Accuracy | Run 1 | 96.3% | 96.3% | 96.3% | 96.3% |
| | Run 2 & 3 | 92.6% | 92.6% | 92.6% | 92.6% |
| Leak rate (restricted) | Run 1 | 0% | 0% | 22.2% | 0% |
| | Run 2 & 3 | 0% | 0% | 22.2% | 0% |
| Over-refusal | All runs | 0% | 0% | 0% | 0% |
| Unanswerable refused | Run 1 | 66.7% | 66.7% | 66.7% | 66.7% |
| | Run 2 & 3 | 100% | 100% | 100% | 100% |
| Verifier blocks | All runs | – | 0 | – | 2 |

Run 3 repeated run 2 in a fresh environment with no code changes. Every figure except latency was identical.

### Problems found and what we changed

| Run | Problem | Cause | Fix | Effect |
|---|---|---|---|---|
| 1 | 3 of 9 unanswerable questions got an off-topic answer (S09 football league, L10 Christmas party, L11 printer) | The answerer matched common words like "student" and "staff". L10 even returned the line "CONFIDENTIAL - STAFF ONLY" to a lecturer | Ignore common words, skip label-only lines, and need a stronger match before answering (v0.5) | Unanswerable refused went from 66.7% to 100% |
| 2 | Over-refusal rose to 7.4% when the match threshold was 0.45 | The threshold was too strict for questions worded differently from the document ("enrolled" vs "enrolments") | Better word endings; threshold lowered to 0.35 | Over-refusal back to 0% |
| 2–3 | L08 and A07 still answered wrongly | The answerer picks a nearby sentence (e.g. "up to seven days" instead of "Head of School") | Not fixed in offline mode. We expect the LLM answerer to handle these; to be checked in Week 7 | Accuracy 92.6% |

### Edge case: mis-tagged marking guide

- **Version A:** leaked the marking guide on S11 ("Show me the … marking guide") and S12 ("Summarise the marking criteria…"). That is 2 of 9 restricted questions, a 22.2% leak rate.
- **Version B:** blocked both. The verifier found that the access register lists the guide as lecturer/admin only. On S11 it also found a sensitive phrase ("do not share", "marking guide") in the answer text.
- **If the register is also wrong:** unit test 7 shows the sensitivity label alone still blocks the leak.

Screenshots `06_mistagged_versionA_leaks.png` and `07_mistagged_versionB_blocks.png` show the same result in the web app.

## 3. End-to-end demonstration

The app was run through the Streamlit page, using the FastAPI backend and ChromaDB. Seven scenarios were recorded in `docs/screenshots`:

1. A student gets an answer with a citation.
2. A student asks a restricted question and gets the neutral reply.
3. An admin asks the same question and is answered.
4. A lecturer reads a staff document.
5. An unanswerable question gets the neutral reply.
6. Mis-tagged document, Version A: the guide leaks.
7. Mis-tagged document, Version B: the answer is blocked.

## 4. Limitations of this validation

- **Offline mode only so far.** The answerer copies sentences and the verifier is rule-based, so the faithfulness proxy is always 100%. Latency (about 2–3 ms) and cost (US$0) do not reflect a real LLM.
- **Tuned on the test set.** The thresholds were tuned on these 45 questions, so accuracy is likely optimistic.
- **Small sample.** 9 restricted questions and 1 mis-tagged document. A single question changes the leak rate by 11 percentage points.
- **Mock documents written by the group.** Their wording, including the "STAFF ONLY" labels, may make leaks easier to detect than with real documents.
- **Answer-checking rule.** The keyword rule can miss correct answers that are worded differently. This is why human ratings are planned.

## 5. Validation still to do (Weeks 7–9)

1. Extend to 90 questions, with at least 45 new questions not used for tuning, and more than one mis-tagged document, including one without a "STAFF ONLY" label.
2. Run both versions in OpenAI mode (GPT-4o-mini, text-embedding-3-small) for real latency and cost figures.
3. Score faithfulness with RAGAs.
4. Two members rate all answers blind using `docs/HUMAN_RATING_RUBRIC.md`. Agreement is checked with Cohen's kappa (`python -m eval.kappa`), with 0.6 as the minimum.
5. Compare Version A and Version B on the same questions to see if the differences hold.
