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
| v1.2 | 16 Nov 2026 | Real corpus: 16 public policies from UOW, UOW Dubai, Heriot-Watt, UNSW, fetched by script with hashes, + real question set (`d7af1ca`); `RAG_CORPUS` switch (`f3b06e7`); run 6 (`411e988`); repeatable vector search (`ef7a2bc`); label-form sensitivity markers + run 7 (`4a29adb`); real-corpus CI job (`4315a58`); document upload API and Documents & embeddings tab (`387e672`, `624b752`) (Nikita) | Group needed a real dataset. Run 6 on real text: B over-refusal 17.9% from "confidential" in public policies, and non-repeatable search; both fixed. Run 7: B = A accuracy (78.6%), twice the unanswerable refusals, no leaks |
| v1.3 | 16 Nov 2026 | Plain-language web page (`20564b5`); TOC and navigation text removed from the real documents, run 8 (`3b8fe35`); screenshots retaken (Nikita) | Nikita found the page hard to understand. Testing the new page on the real corpus showed TOC lines outranking real text, so the mis-tag demo did not work there; fixed, run 8 keeps accuracy and makes A's leaks clearer (8/8 vs B 0/8) |
| v1.4 | 16 Nov 2026 | Dataset choice: chunks carry their university, retriever filters on it, `/datasets` (`8adb95b`); pop-up with university logos before the first question (`4ed9f81`) (Nikita) | Nikita's idea: pick whose documents answers come from. Evaluation unchanged (no dataset = all). Found a verifier gap: a UOW answer to a Heriot-Watt question is approved |
| v1.5 | 16 Nov 2026 | Real question set 2 frozen first (`0e570d6`); verifier rejects sources from a university the question does not name (`49b7773`); run 9 (`dd6bcc9`); sources labelled real/mock (Nikita) | v1.4 gap closed: traps refused B 14/15 vs A 1/15 on new questions; Nikita asked whether an answer was real, so origins are now shown |
| v1.6 | 16 Nov 2026 | dubai corpus: 7 more universities with Dubai campuses, campuses merged under Dubai (`0196437`); dubai question set frozen (`a622f5b`); register fix after invalid run 10 (`a76b9b7`); run 11 (`f8233c2`); pop-up and examples for 11 universities (Nikita) | Nikita asked for a Dubai-market focus. Run 11: traps refused 7/8 vs 1/8; new false alarm from 'marking guide' in Curtin's manual |

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
- **Real public documents, mock restricted ones (v1.2):** real restricted documents are not public;
  the real public documents still test retrieval at scale and whether the verifier blocks real text.
- **Do not commit the universities' texts (v1.2):** store the source list, the fetch script and text
  hashes instead, so the corpus can be rebuilt and changes detected.
- **Labels must look like labels (v1.2):** the word "confidential" in a sentence is not a label.
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

### Session log, part 3 (v1.2, same day)

| Step | What was done | Result | Commit |
|---|---|---|---|
| 17 | Searched for public policies on the same topics; checked all 16 URLs download | UOW 6, UOW Dubai 2, Heriot-Watt 6, UNSW 2 | `d7af1ca` |
| 18 | Wrote the fetch/extract script; fixed an extraction bug (an unclosed `<button>` hid the UNSW page) | About 58,600 words; hashes recorded | `d7af1ca` |
| 19 | Wrote 45 real questions; checked every keyword is in its document; committed before any run | 28 / 9 / 8 | `d7af1ca` |
| 20 | Run 6 with the v1.1 system unchanged | B over-refusal 17.9% ("confidential" in 9 public policies) | `411e988` |
| 21 | Noticed A differed between identical indexes; reproduced (1 of 45 questions) | Fixed with ef_search and tie-breaking; 5 rebuilds identical; run 6 re-run | `ef7a2bc` |
| 22 | Label-form markers; run 7 | B = A accuracy, over-refusal 3.6%, no leaks | `4a29adb` |
| 23 | Document upload (idea from Nikita): preview, add, delete; checked by hand in the browser | Screenshot 10 | `387e672`, `624b752` |

### Session log, part 4 (v1.3, same day)

| Step | What was done | Result | Commit |
|---|---|---|---|
| 24 | Nikita: "very complex, not clear how it works". Rewrote the Ask page in plain language | Pipeline strip, verdict boxes, "How this answer was made", Advanced section | `20564b5` |
| 25 | Tested every example on the real corpus in the browser | Mis-tag demo found nothing: TOC lines outranked the guide; A returned UOW navigation text | – |
| 26 | Dropped TOC/navigation text in `fetch_real`, re-extracted, new hashes; run 8 | Same accuracy; leaks A 8/8 vs B 0/8; demo works | `3b8fe35` |
| 27 | Retook screenshots 08 and 09 with the new page | – | this commit |

### Session log, part 5 (v1.4, same day)

| Step | What was done | Result | Commit |
|---|---|---|---|
| 28 | Looked for official logos; asked Nikita before downloading; downloaded UOW, UNSW, Heriot-Watt logos locally (not committed); UOW Dubai blocks downloads, monogram used | `assets/logos/` git-ignored | `8adb95b` |
| 29 | University field on chunks, dataset filter, `/datasets`; evaluation re-checked | Mock = run 5, real = run 8 | `8adb95b` |
| 30 | Dataset pop-up; tested in the browser (HW, Change, UOW) | Verifier gap found: wrong-university answer approved | `4ed9f81` |

## Next steps (Weeks 7–9)

1. ~~Extend the test set to 90 questions, with at least 45 new questions not used for tuning.~~ Done (v0.12).
2. Run both versions in `openai` mode and add RAGAs faithfulness scores. Report the held-out set as the main result.
3. Two members rate answers blind using the rubric; report Cohen's kappa.
4. ~~Decide whether to add a relevance check to the verifier (run 4 finding).~~ Added in v1.1, tested on held-out set 2. Measure the LLM judge version in `openai` mode.
5. Group review of this fork, then merge it into the group repository (pull request).
6. Update Figure 1 to show the access register and source-document check (the README diagram already does).
7. ~~Verifier: compare the university named in the question with the source's university.~~ Done in v1.5 (run 9).
8. Offline relevance rules missed two correct answers on real set 2 ("periods", coverage 0.24); revisit with a new question set.
9. ~~Corpus v2: more Dubai universities, campuses merged under the Dubai campus.~~ Done in v1.6 (run 11).
10. Content phrases ("marking guide") also give false alarms on real documents (run 11); make them document-label checks like v1.2 did for access labels, and test on a new question set.
11. Clean PDF page headers such as "CUD - UG Student Handbook ... Page 14 of 23" in the next corpus version.
