"""Answerer agent: writes an answer using only the retrieved chunks, with citations.

Offline mode is extractive (picks the best-matching sentences); openai mode uses the LLM.
"""
import re

from .. import config
from ..embeddings import _stem, tokens

SYSTEM = (
    "You answer university questions using ONLY the numbered sources provided. "
    "Cite every sentence with its source number in square brackets, e.g. [1]. "
    "If the sources do not answer the question, reply exactly: " + config.NEUTRAL_REPLY
)


def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


# Words that appear in almost every document, so matching on them says nothing (found in run 1).
GENERIC = {_stem(w) for w in "student students staff university subject session uni campus year".split()}
LABEL_ONLY = re.compile(r"^(confidential|staff only|admin only|hr confidential|[\s\-.])+$", re.I)


def _overlap(q, s):
    qs = {_stem(t) for t in tokens(q)} - GENERIC
    ss = {_stem(t) for t in tokens(s)} - GENERIC
    return len(qs & ss) / (len(qs) or 1)


class Answerer:
    def __init__(self, llm=None):
        self.llm = llm

    def run(self, question, chunks, feedback=None):
        usable = [c for c in chunks if c["score"] >= config.MIN_SCORE]
        if not usable:
            return {"answer": config.NEUTRAL_REPLY, "citations": [], "usage": {}}
        if self.llm:
            return self._llm(question, usable, feedback)
        return self._extractive(question, usable)

    def _extractive(self, question, chunks):
        cands = []
        for c in chunks:
            for s in split_sentences(c["text"]):
                if LABEL_ONLY.match(s):
                    continue
                cands.append((_overlap(question, s) + 0.3 * c["score"], s, c))
        cands.sort(key=lambda x: -x[0])
        if not cands or cands[0][0] < 0.35:
            return {"answer": config.NEUTRAL_REPLY, "citations": [], "usage": {}}
        # keep a second sentence only if it matches nearly as well as the best one
        picked = [cands[0]] + [x for x in cands[1:2] if x[0] >= 0.8 * cands[0][0]]
        if not picked:
            return {"answer": config.NEUTRAL_REPLY, "citations": [], "usage": {}}
        used, parts = [], []
        for _, s, c in picked:
            if c["id"] not in [u["id"] for u in used]:
                used.append(c)
            n = [u["id"] for u in used].index(c["id"]) + 1
            parts.append(f"{s} [{n}]")
        words = sum(len(c["text"].split()) for c in chunks) + len(question.split())
        usage = {"tokens_in": int(words * 1.3), "tokens_out": int(len(" ".join(parts).split()) * 1.3), "cost_usd": 0.0}
        return {"answer": " ".join(parts), "citations": used, "usage": usage}

    def _llm(self, question, chunks, feedback):
        src = "\n".join(f"[{i + 1}] ({c['title']}) {c['text']}" for i, c in enumerate(chunks))
        user = f"Sources:\n{src}\n\nQuestion: {question}"
        if feedback:
            user += f"\n\nA reviewer rejected your previous answer: {feedback}\nRewrite it using only the sources."
        text, usage = self.llm.chat(SYSTEM, user)
        if config.NEUTRAL_REPLY in text:
            return {"answer": config.NEUTRAL_REPLY, "citations": [], "usage": usage}
        cited = sorted({int(n) for n in re.findall(r"\[(\d+)\]", text) if 0 < int(n) <= len(chunks)})
        used = [chunks[n - 1] for n in cited] or chunks
        # renumber citations to match the order of `used`
        mapping = {n: i + 1 for i, n in enumerate(cited)}
        text = re.sub(r"\[(\d+)\]", lambda m: f"[{mapping.get(int(m.group(1)), m.group(1))}]", text)
        return {"answer": text, "citations": used, "usage": usage}
