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

## Next steps (Weeks 7–9)

1. Extend the test set to 90 questions, with at least 45 new questions not used for tuning.
2. Run both versions in `openai` mode and add RAGAs faithfulness scores.
3. Two members rate answers blind using the rubric; report Cohen's kappa.
