# Development log

| Version | Date | What changed | Why / evidence |
| --- | --- | --- | --- |
| v0.1 | 27 Oct 2026 | 12 mock documents, role-tagged ingestion into ChromaDB, role-filtered retriever | Role filter inside the vector query so restricted chunks never reach the LLM (design decision from AFR [7]) |
| v0.2 | 27 Oct 2026 | Answerer, verifier, orchestrator (Version A/B), query logger | Tutor feedback: the verifier must not rely on the same tags. Added `data/access_register.csv` and sensitivity markers as independent checks |
| v0.3 | 27 Oct 2026 | FastAPI backend and Streamlit UI | Matches the architecture (Figure 1) |
| v0.4 | 27 Oct 2026 | 45-question pilot test set, evaluation runner, run 1 | Run 1 found 3 unanswerable questions answered off-topic (see `results/run1/NOTES.md`) |
| v0.5 | 27 Oct 2026 | Answerer ignores generic words and label-only lines; stronger match needed; 10 unit tests; run 2 | Unanswerable refused 66.7% → 100%; mis-tagged leak A 22.2% vs B 0% (see `results/run2/NOTES.md`) |
| v0.6 | 27 Oct 2026 | Demo URL parameters, screenshots | Evidence that the artefact runs end to end |
| v0.7 | 27 Oct 2026 | README, AI-use declaration, human rating rubric, Cohen's kappa script | Tutor feedback: specify models, rubric and agreement method |
| v0.8 | 10 Nov 2026 | Testing and validation report (`docs/TESTING.md`); run 3 reproduction check in a fresh environment | Tutor feedback: give a detailed testing and validation section. Run 3: 10/10 tests pass and all results match run 2 |
| v0.9 | 10 Nov 2026 | Signed login tokens: the API reads the role from the server-issued session, not the request; 4 API tests; access-control, test-data, sample-size and parameter documentation | Tutor questions: how the verifier gets the user's metadata, test data sets, why 30 questions, parameter adjustments |
| v0.10 | 16 Nov 2026 | Pinned requirements; chromadb embedding protocol; random token key; API request validation and empty-index check; UI error handling and re-login (`d6ad515`–`6f9f9bf`, Nikita) | Found by testing the running API and web page by hand (see session log below). Tests 15–22 |
| v0.11 | 16 Nov 2026 | Verifier checks labels in the whole source document; answerer adds a second sentence only from the same document; `--mistag DOC_ID ...` (`9bf9322`–`f7d9469`, Nikita) | New test mis-tagged each restricted document with a wrong register: B still leaked 2 of 6. Committed as expected failure first, then fixed. Tests 23–29 |
| v0.12 | 16 Nov 2026 | 45 held-out questions, unlabelled restricted document, four conditions, 95% intervals, McNemar test, GitHub Actions CI; run 4 (`1a5d9e9`–`c3f1248`, Nikita) | Open items from 10 Nov: 90 questions, more mis-tagged documents incl. one without a label. Held-out accuracy 76.0% vs 92.6%; verifier checks faithfulness, not relevance; single mis-tag p = 0.5 |
| v1.0 | 16 Nov 2026 | Testing report, access-control, AI-use and README updates; this log (`512c49d` onwards, Nikita) | Documentation matches the code and the run 4 results |
| v1.1 | 16 Nov 2026 | Second held-out set frozen first (`26a3e44`); verifier checks every chunk the answerer saw (`1cfdc32`); relevance check and separate rewrite budget for leak removal (`e99915c`); run 5 (`37074f3`); API source text, index status, demo re-index (`8756ddf`); new web page with A/B compare (`14e8ddc`) (Nikita) | Run 4 finding: the verifier passed off-topic answers. Reproduced an uncited-context leak with a fake LLM client. Held-out 2: unanswerable refused B 26.7% vs A 13.3%, accuracy and over-refusal unchanged, no leaks added |

## Design decisions

- **Role filter inside retrieval, not after:** a post-filter would let restricted chunks reach the LLM.
- **Verifier uses an independent access register:** a mis-tagged chunk passes the retriever's filter, so
  the verifier needs a source of truth that is not the vector-DB tag.
- **Fail closed:** a document missing from the register is treated as restricted.
- **Revise before block:** if the verifier finds a bad source, the answerer tries once more without it, so
  a safe partial answer is not thrown away. Only if nothing safe is left is the neutral reply returned.
- **Same neutral reply for "restricted" and "not in the documents":** so a user cannot tell whether
  restricted information exists.
- **Offline mode:** lets every member run and test the code with no API key or cost.

- **Check labels in the whole source document (v0.11):** a label is written once, so only the first chunk
  had it. The document text is read from `data/docs`, so the check is still independent of ChromaDB.
- **Check every chunk the answerer saw (v1.1):** an LLM can copy a fact from one source and cite
  another, so the leak checks cannot rely on the citations.
- **Relevance is part of "correct" (v1.1):** the research question counts wrong answers, and an
  off-topic answer is a wrong answer even if every word is copied from a source.
- **A new held-out set for every change made after looking at a held-out set (v1.1):** held-out 1
  was used to design the relevance check, so held-out 2 was committed before the change and run once.
- **Freeze parameters before the held-out run (v0.12):** the held-out questions were run once, after all
  fixes, and nothing was changed after seeing the results, so they stay a fair test.

## Session log: 16 Nov 2026 (Nikita Dvornitsyn, with Claude Code)

Starting point: upstream v0.9 (`4f5e8d2`), forked to `ma3str0o0/role-aware-rag-assistant`. Steps 1–4 were testing before any change; exact times of the changes are in the commit history (`git log`).

| Step | What was done | Result | Commit |
|---|---|---|---|
| 1 | Fresh install, `pytest`, `python -m eval.run_eval` | 14/14 pass; run 3 figures reproduced; 5 deprecation warnings from chromadb | – |
| 2 | Probed the pipeline: each restricted document mis-tagged with the register also wrong | Version B leaked `staff_exam_moderation` and `admin_enrolment_report`: labels only in chunk #0 | `9bf9322`, `fcc15f5` |
| 3 | Probed the API with a test client | Hard-coded token key; empty / 100k-char questions accepted; empty index reported as `ok` | `38b439d`, `d423466` |
| 4 | Ran the API and Streamlit page in a browser | Extra unrelated sentence ("per day"); crash on `?user=hacker`; traceback with the API down | `f7d9469`, `6f9f9bf` |
| 5 | Pinned requirements, pytest config, chromadb protocol | Tests pass with deprecation warnings as errors | `d6ad515`, `b05c037` |
| 6 | Re-tested UI by hand after the fix | Bad URL params fall back, API-down message, automatic re-login after API restart | `6f9f9bf` |
| 7 | Wrote 45 held-out questions and the unlabelled document | 90 questions: 52 / 18 / 20 as planned | `1a5d9e9` |
| 8 | Run 4: 2 sets × 4 conditions × 2 versions = 720 answers | See `results/run4/NOTES.md` | `760ceef` |
| 9 | GitHub Actions CI | Green on Python 3.11 and 3.12; run 4 reproduced on a clean machine | `c3f1248` |
| 10 | Documentation | – | `512c49d` |

### Session log, part 2 (v1.1, same day)

| Step | What was done | Result | Commit |
|---|---|---|---|
| 11 | Wrote and committed held-out set 2 before touching the verifier, and pushed it | Commit time on GitHub shows it came first | `26a3e44` |
| 12 | Fake LLM client: answer copies the mis-tagged guide but cites a public chunk | Version B passed it; fixed by checking all context | `1cfdc32` |
| 13 | Feature analysis of off-topic answers on the development sets (coverage, answer type) | Coverage alone does not separate them; type + coverage < 0.25 removes 6 wrong, 0 correct | `e99915c` |
| 14 | Development run with the relevance check | With all documents mis-tagged, over-refusal 20% vs 12%: leak removal used the only rewrite; fixed with a separate budget | `e99915c` |
| 15 | Run 5, one run on held-out set 2 | Small gain on unanswerable, no cost; leaks unchanged | `37074f3` |
| 16 | New web page, checked by hand in the browser (compare mode, live mis-tag, off-topic case) | Screenshots 08 and 09 | `14e8ddc` |

## Next steps (Weeks 7–9)

1. ~~Extend the test set to 90 questions, with at least 45 new questions not used for tuning.~~ Done (v0.12).
2. Run both versions in `openai` mode and add RAGAs faithfulness scores. Report the held-out set as the main result.
3. Two members rate answers blind using the rubric; report Cohen's kappa.
4. ~~Decide whether to add a relevance check to the verifier (run 4 finding).~~ Added in v1.1, tested on held-out set 2. Measure the LLM judge version in `openai` mode.
5. Group review of this fork, then merge it into the group repository (pull request).
6. Update Figure 1 to show the access register and source-document check (the README diagram already does).
