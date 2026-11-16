# Changelog

Versions v0.1–v0.9 are described in `docs/DEVELOPMENT_LOG.md`. Each version below is tagged in git.

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
