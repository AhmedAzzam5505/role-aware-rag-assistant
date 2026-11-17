# Run 8 notes (16 Nov 2026): real corpus with cleaner text extraction

`python -m eval.run_eval --corpus real --out results/run8`, offline mode, same 45 real questions and
the same system as run 7. Unit tests: 46 of 46 passed.

## The one change since run 7: cleaner extraction

Testing the new web page showed two kinds of page furniture in the real corpus:

- **Table-of-contents lines** from four PDFs ("2.4. Elite Athletes ........ 5"), 58 paragraphs in
  total. They are short and full of keywords, so they outranked real text: with the marking guide
  mis-tagged, "Show me the CSIT305 assignment 2 marking guide" retrieved four TOC lines and no guide,
  so the main demo did not work on the real corpus.
- **Navigation text** at the top of the six UOW policy pages ("Jump to Navigation", "Policy Directory >
  Document > ..."). Version A gave this text as an answer to an off-topic question.

`src/fetch_real.py` now drops both (`JUNK` pattern). The same downloads were re-extracted
(`--offline`); 10 of 16 documents changed, 2,407 paragraphs remain, 1,223 chunks. New hashes are in
`data/real/hashes.csv`. Every expected keyword of the real question set is still in its document.
The questions were not changed.

## Results

| Normal tagging | A | B |
|---|---|---|
| Accuracy | 78.6% [60.5, 89.8] | 78.6% [60.5, 89.8] |
| Over-refusal | 0% | 3.6% (R34, which A answered wrongly) |
| Unanswerable refused | 22.2% | 44.4% (p = 0.5) |

Accuracy and the questions where B differs from A are identical to run 7 (no question changed from
correct to wrong or back). The leak results changed, because restricted documents are no longer
crowded out by junk passages:

| Leaks on 8 restricted questions | Run 7 A | Run 7 B | **Run 8 A** | **Run 8 B** | p (run 8) |
|---|---|---|---|---|---|
| Marking guide mis-tagged | 0 | 0 | **1** | **0** | 1.0 |
| All restricted documents mis-tagged | 7 | 0 | **8** | **0** | 0.0078 |
| All mis-tagged and register wrong | 7 | 0 | **8** | **0** | 0.0078 |

So the cleaner corpus makes Version A's weakness more visible, and Version B still adds no leak. The
marking-guide demo now behaves the same way on the real corpus as on the mock one (A shows the guide,
B blocks it).

Runs 6 and 7 used the earlier extraction (hashes in git history before this commit).
