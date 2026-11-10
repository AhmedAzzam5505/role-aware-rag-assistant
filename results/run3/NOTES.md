# Run 3 notes (10 Nov 2026): reproduction check

No code changes since run 2. We set up a fresh environment from `requirements.txt`
(Python 3.13, ChromaDB 1.5.9, FastAPI 0.162, Streamlit 1.67), rebuilt the index and re-ran
everything to check the results can be reproduced.

- Unit tests: 10 of 10 passed (`unit_tests.txt`).
- Evaluation: every accuracy, leak, refusal and verifier figure is identical to run 2. Only the
  latency figures differ slightly, as expected between machines.
- The same two answerable questions are still wrong (L08, A07), which confirms they are real
  weaknesses of the offline answerer and not random.
