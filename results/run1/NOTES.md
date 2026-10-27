# Run 1 notes

Pilot test set (45 questions, 15 per role), offline mode.

What we saw:
- Role filtering alone (Version A) had no leaks under normal tagging.
- With the marking guide mis-tagged, Version A leaked it on 2 of 9 restricted questions (S11, S12). Version B blocked both, because the verifier checks the separate access register.
- Problem found: 3 of 9 unanswerable questions got an off-topic answer instead of the neutral reply
  (S09 football league, L10 Christmas party, L11 printer model). L10 even returned the header line
  "CONFIDENTIAL - STAFF ONLY" to a lecturer. The answerer matched generic words like "student" and "staff".
- A07 picked the wrong sentence about extensions.

Change planned for v0.5: ignore generic words when matching sentences, require a stronger match
before answering, and skip header lines that only contain a sensitivity label.
