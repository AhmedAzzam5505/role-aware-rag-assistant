# Datasets

The project uses two document corpora and five question sets. This page says where each comes from,
how to rebuild it and what it can and cannot show.

## 1. Corpora

| Corpus | Documents | Chunks | Used for |
|---|---|---|---|
| `mock` (default) | 13 documents written by the group: 6 public, 4 staff-only, 3 admin-only (`data/docs/`) | 29 | Development, runs 1–5, unit tests |
| `real` | 16 public policy documents from four universities (`data/real/`) + the 7 mock staff/admin documents | 1,223 | Runs 6–8: does the system work on real university text? |

Select one with `RAG_CORPUS=mock|real` (API, ingestion) or `python -m eval.run_eval --corpus real`.

### 1.1 Real public documents

All 16 are public web pages or PDFs, retrieved on 16 Nov 2026. They cover the same topics as the mock
public documents, so the same kinds of questions apply.

| University (country) | Documents | Topics |
|---|---|---|
| University of Wollongong (Australia) | 6 | academic consideration policy and guidelines, assessment and feedback (late penalties), review and appeal of academic decisions (policy and procedures), academic integrity |
| University of Wollongong in Dubai (UAE) | 2 | academic integrity policy, fee policy (refunds, late payment, reinstatement) |
| Heriot-Watt University (UK) | 6 | mitigating circumstances (web page and student guide), coursework submission and late penalty, academic misconduct, academic appeals, temporary suspension of studies |
| UNSW Sydney (Australia) | 2 | special consideration and short extensions (web page and guidelines) |
| **Total** | **16** | 2,407 paragraphs, about 58,000 words |

The full list with URLs is `data/real/manifest.csv`.

**Why the texts are not in the repository.** The documents belong to their universities. The
repository therefore stores only the list of sources and the code that builds the corpus:

```bash
python -m src.fetch_real              # download, extract text, write data/real/docs/*.md (git-ignored)
RAG_CORPUS=real python -m src.ingest  # build the real index
```

`src/fetch_real.py` extracts the main text of HTML pages (navigation, scripts and repeated menus
removed) and of PDFs (with `pypdf`, lines re-joined into paragraphs). Table-of-contents lines and page
navigation text are dropped (since run 8: they outranked real text in search). Every document is marked
`public` and visible to all roles in `data/real/access_register.csv` (owner = the university).

**Reproducibility.** `data/real/hashes.csv` stores a SHA-256 of each extracted text as used for run 8
(runs 6–7 used an earlier extraction; their hashes are in the git history). Re-running the fetch prints `same` or `CHANGED` for each document, and the optional
`real-corpus` job in GitHub Actions does this on every push and re-checks run 8 when nothing changed.
If a university updates a page, results on the real corpus may differ; the mock corpus is unaffected.

### 1.2 Restricted documents stay mock

Real staff-only or admin-only documents (marking guides, salary bands, misconduct registers) are not
public, and using them would be neither possible nor ethical. The real corpus therefore keeps the 7
mock restricted documents, and every leak test uses them. The real public documents make retrieval
harder (more, longer and more similar chunks) and test whether the verifier wrongly blocks real
public text, which is what run 6 found (see `results/run6/NOTES.md`).

## 2. Question sets

| File | Corpus | Answerable / unanswerable / restricted | Status |
|---|---|---|---|
| `eval/test_set.csv` (pilot) | mock | 27 / 9 / 9 | tuned on (v0.5) |
| `eval/test_set_holdout.csv` | mock | 25 / 9 / 11 | fair test in run 4, then a development set for v1.1 |
| `eval/test_set_holdout2.csv` | mock | 22 / 15 / 8 | frozen before v1.1, fair test in run 5 |
| `eval/test_set_real.csv` | real | 28 / 9 / 8 | committed before any run on the real corpus (runs 6–8) |

Every row has the user's role, the question type, the expected document and a keyword the answer must
contain. In the real set, questions name the university ("At UOW, ..."), and `|` separates accepted
alternatives when a fact appears in two documents or is worded two ways (e.g. `3 working days|three
working days`). A script checked that every expected keyword occurs in its document; the unanswerable
questions were checked by searching the documents for their key terms.

The questions were written with AI help (see `docs/AI_USE_DECLARATION.md`) from the documents
themselves, so they are probably easier than questions real students would ask. Human ratings
(`docs/HUMAN_RATING_RUBRIC.md`) and questions collected from students would make the evaluation
stronger.

## 3. Uploaded documents

The web page's "Documents & embeddings" tab lets anyone preview how a document is chunked and embedded,
and lets lecturers and admins add it to the running index. Uploads are never part of a corpus or of
the evaluation, and they disappear when the index is rebuilt.
