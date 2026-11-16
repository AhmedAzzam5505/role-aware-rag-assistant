# Changelog

Versions v0.1–v0.9 are described in `docs/DEVELOPMENT_LOG.md`. Each version below is tagged in git.

## v1.4 (16 Nov 2026)
- Choose the dataset: a pop-up before the first question with a card per university (logo, country, documents the role can search) and "All universities"; answers are built only from the chosen university's documents (plus uploads). `POST /ask` takes `dataset`; new `GET /datasets`.
- Chunks carry a `university` field (re-ingest needed). In the real corpus the mock staff/admin documents count as UOW Dubai internal documents.
- Official logos are read from `assets/logos/` (git-ignored); missing ones are drawn as monograms.

## v1.3 (16 Nov 2026)
- Web page rewritten in plain language: five-step pipeline strip, "Who are you?" and "How to show answers" in the sidebar, side-by-side "Without checker / With checker" by default, a verdict box per answer (approved, fixed, blocked with the reason, no answer, not checked, leak), "How this answer was made" in numbered steps, technical details and demo controls under Advanced, examples with the expected behaviour for each corpus.
- Real corpus: table-of-contents and page-navigation text removed during extraction (they outranked real text); new hashes; run 8. The real-corpus CI job checks run 8.

## v1.2 (16 Nov 2026)
- Real corpus: 16 public policy documents from the University of Wollongong, UOW Dubai, Heriot-Watt and UNSW (`data/real/manifest.csv`), built by `python -m src.fetch_real` (texts not committed; SHA-256 hashes in `data/real/hashes.csv`), plus the mock restricted documents. `RAG_CORPUS=mock|real`.
- Real question set (`eval/test_set_real.csv`, 45 questions); runs 6 and 7; `docs/DATASET.md`.
- Verifier: access labels count only in label form (upper case). The word "confidential" in real public policies made Version B refuse correct answers.
- Retriever: repeatable search on large indexes (HNSW `ef_search` 2000, ties broken by chunk id).
- Document upload: `POST /documents/preview`, `POST/GET/DELETE /documents`, and a "Documents & embeddings" tab showing chunks, vectors, features and similarity to a question.
- CI: optional job that fetches the real corpus and checks run 7. New dependency: `pypdf`.

## v1.1 (16 Nov 2026)
- Verifier: leak checks cover every chunk the answerer saw, not only cited ones (an LLM answer could copy a restricted fact and cite a public source).
- Verifier: relevance check. LLM judge returns `answers_question`; offline rules check the answer type and question coverage (`REL_MIN_COVERAGE`). Off-topic answers are rewritten once, then blocked.
- Orchestrator: removing leaked sources no longer uses up the quality rewrite (`MAX_TOTAL_REVISIONS = 2`).
- Second held-out set (`eval/test_set_holdout2.csv`), frozen before the verifier changes; run 5 with a paired test for unanswerable refusals; CI checks against run 5.
- API: cited source text, `restricted_for_role` flag, index status in `/health`, `POST /demo/reindex` with `DEMO_MODE=1`.
- Web page rebuilt: chat history, A/B side-by-side comparison, verifier badges, source text, scenarios per role, readable agent trace, live mis-tag switch.

## v1.0 (16 Nov 2026)
- Documentation updated for run 4: testing report, access control, AI-use declaration, README, development log.

## v0.12 (16 Nov 2026)
- 45 held-out questions (`eval/test_set_holdout.csv`), 90 in total (52 answerable / 18 unanswerable / 20 restricted).
- New restricted document with no sensitivity label (`staff_lecturer_workload`).
- Evaluation conditions: `mistagged_all`, `mistagged_all_bad_register`.
- 95% Wilson intervals and paired exact McNemar test (`eval/stats.py`).
- GitHub Actions: tests on Python 3.11/3.12 and a check that the evaluation reproduces `results/run4`.

## v0.11 (16 Nov 2026)
- Verifier: sensitivity labels are checked in the whole source document, not only the chunk (closed a leak when tag and register are both wrong).
- Answerer: a second sentence is added only from the same document.
- `python -m src.ingest --mistag DOC_ID ...` mis-tags any documents.

## v0.10 (16 Nov 2026)
- Security: the token signing key is no longer hard-coded; set `SESSION_SECRET` or a random key is used.
- API: questions must be 1–500 characters, version must be A or B; empty index returns 503 and `/health` shows `no_index`.
- UI: no tracebacks for bad URL parameters, API errors or a stopped API; re-login after token expiry.
- Pinned dependency versions; chromadb 1.x embedding protocol (no deprecation warnings); pytest config.
