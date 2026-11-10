# How the system knows the user's role, and how the verifier checks permissions

## 1. Where the role comes from

| Step | What happens | File |
|---|---|---|
| Login | The server looks up the username in the user directory and finds the role (student, lecturer or admin). In this prototype the directory is three demo accounts. At a university it would be single sign-on. | `src/auth.py` |
| Session token | The server puts the username, role and an 8-hour expiry into a token and signs it with a secret key (HMAC-SHA256). The user cannot change the role without breaking the signature. | `src/auth.py` |
| Each question | The web page sends the question with the token. The API checks the signature and expiry, then reads the role from the token. A `role` field in the request is ignored, and so is anything the user writes in the question ("I'm a lecturer…"). | `api.py` |
| Agents | The orchestrator passes this one role to both the retriever and the verifier. | `src/orchestrator.py` |

Tested in `tests/test_api.py`: requests without a token are rejected, a token whose role was edited is rejected, a `"role": "admin"` field sent by a student is ignored, and an admin token gets the admin answer.

## 2. What metadata the retriever and the verifier each use

| | Retriever | Verifier |
|---|---|---|
| User's role | From the session (via the orchestrator) | From the session (via the orchestrator) |
| Document permissions | The `role_<role>` tags stored with each chunk in ChromaDB | The **access register** (`data/access_register.csv`): which roles may see each document, kept by the document owner |
| Document content | The chunk text, used for search | The cited chunk text and the draft answer, checked for sensitivity labels ("STAFF ONLY", "CONFIDENTIAL", …) |
| Uses the ChromaDB role tags? | Yes | **No.** It only uses the chunk's `doc_id` to look the document up in the register |

Because the verifier never reads the role tags that the retriever relies on, a document tagged wrongly in ChromaDB is still caught. If a document is missing from the register, the verifier treats it as restricted.

## 3. In a real deployment

The register would be read from the university's document-management permissions (for example, SharePoint or LMS access lists) through a read-only service account, not from a CSV file. Only document owners could change it, and the database ingestion team could not.
