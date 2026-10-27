# AI-use declaration

| Where GenAI was used | Tool | What it produced | How we verified it |
| --- | --- | --- | --- |
| Literature search and summaries | Claude (Anthropic) | Candidate papers and short summaries | Every paper was opened and checked by the group; DOIs and page numbers were checked on the publisher site; papers we could not open were not cited |
| Drafting and editing the milestone document | Claude | Draft wording for sections, which we then edited | The group read every section, checked claims against the cited papers and changed wording to our own |
| Architecture diagram | AI image/diagram tool, from our own design prompt (prompt in the evidence log) | Figure 1 | Checked every box and arrow against our design |
| Prototype code (this repository) | Claude, working from our architecture, methodology and evaluation plan | Python code for ingestion, the three agents, API, UI, tests and the evaluation runner | We ran the 10 unit tests (all pass), ran the evaluation twice, read the failures in the result files and confirmed the fixes in the second run; the commit history shows each iteration |
| Mock documents and pilot test questions | Claude, from our list of document types and question types | 12 mock documents and 45 questions | We checked that each question's expected answer and source really appear in the documents; all content is invented, no real university data |

**Not done by AI:** the choice of topic, research question, the design decisions recorded in the
evidence log, the human ratings (Weeks 8–9), and the final interpretation of results.

**Limitations of AI use:** AI-written code and text can contain mistakes. We reduce this by running the
tests and evaluation ourselves and checking every reference by hand. The runtime models used *inside*
the prototype (GPT-4o-mini and text-embedding-3-small in `openai` mode) are part of the system being
studied, not help with writing the project.
