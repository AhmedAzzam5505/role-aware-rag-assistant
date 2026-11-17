"""Offline relevance check used by the verifier (added in v1.1).

Run 4 showed that a sentence copied from a source is always "supported", even when it does not
answer the question ("What is the Wi-Fi password for guests?" -> "IT Services helps with ... Wi-Fi
access"). The verifier therefore also asks: does the answer address the question?

In openai mode the LLM judge answers that directly. Offline, two simple rules are used:

1. Answer type. If the question asks for a number ("how many"), a duration ("how long"), a time
   ("when"), a person or body ("who approves ...") or a place ("where"), the answer must contain
   something of that type.
2. Coverage. The share of the question's content words (weighted by how rare they are in the
   documents, IDF) that also appear in the answer must be at least `config.REL_MIN_COVERAGE`.

Both rules were set on the development questions only (pilot set + first held-out set) and frozen
before the second held-out set was run. They are deliberately conservative: on the development
questions they removed six wrong answers and no correct ones, but they cannot tell that "Wi-Fi
access" does not answer "Wi-Fi password". That needs an LLM.
"""
import math
import re

from .. import config
from ..embeddings import _stem, tokens

NUM = r"\b(\d+([.,:]\d+)?%?|one|two|three|four|five|six|seven|eight|nine|ten|twelve|twenty|thirty|thirty-one|half|zero)\b"
ANSWER_TYPES = [
    ("number", r"^(how many|how much|what percentage|what proportion)\b", NUM),
    ("duration", r"^(how long|how quickly|how soon|how far ahead|how often)\b",
     NUM + r"|\b(days?|weeks?|hours?|months?|years?|immediately)\b"),
    ("time", r"^when\b",
     r"\b(january|february|march|april|may|june|july|august|september|october|november|december"
     r"|week|day|days|before|after|within|until|by|am|pm|session|period)\b"),
    ("actor", r"^who\s+(?!is\b|are\b)",
     r"\b(officer|coordinators?|committee|team|head|tutor|registrar|central|services|moderator"
     r"|students?|staff|hr|lecturers?|school|dean)\b"),
    ("place", r"^where\b",
     r"\b(portal|drive|website|moodle|system|office|library|it services|online|through|in the|on the|to the)\b"),
]

# Words that appear in almost every document, so they say nothing about relevance.
GENERIC = {_stem(w) for w in "student students staff university subject session uni campus year".split()}


def body(doc_text):
    """Document text without the front-matter header."""
    parts = doc_text.split("---", 2)
    return parts[2] if len(parts) == 3 else doc_text


class RelevanceChecker:
    def __init__(self, doc_texts, min_coverage=None):
        self.min_coverage = config.REL_MIN_COVERAGE if min_coverage is None else min_coverage
        paras = [p for t in doc_texts.values() for p in body(t).split("\n\n") if p.strip()]
        df = {}
        for p in paras:
            for t in {_stem(t) for t in tokens(p)}:
                df[t] = df.get(t, 0) + 1
        self.n, self.df = len(paras), df

    def idf(self, term):
        return math.log((self.n + 1) / (self.df.get(term, 0) + 0.5))

    def coverage(self, question, answer):
        q = {_stem(t) for t in tokens(question)} - GENERIC
        a = {_stem(t) for t in tokens(answer)}
        total = sum(self.idf(t) for t in q)
        return sum(self.idf(t) for t in q & a) / total if total else 1.0

    def check(self, question, answer):
        """Returns a list of reasons the answer looks irrelevant (empty list = relevant)."""
        answer = re.sub(r"\[\d+\]", "", answer).lower()
        q = question.lower().strip()
        reasons = []
        for name, q_pat, a_pat in ANSWER_TYPES:
            if re.search(q_pat, q):
                if not re.search(a_pat, answer):
                    reasons.append(f"question asks for a {name}, answer has none")
                break
        cov = self.coverage(question, answer)
        if cov < self.min_coverage:
            reasons.append(f"answer covers {cov:.2f} of the question (minimum {self.min_coverage})")
        return reasons
