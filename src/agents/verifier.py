"""Verifier agent: second layer after role-filtered retrieval.

It does NOT trust the role tags stored in the vector database. It checks the draft answer with
information that is kept separately from the retrieval index:

1. Access register (data/access_register.csv): the list of which roles may see each document,
   maintained by the document owners. If a chunk was tagged wrongly when it was uploaded to the
   vector database, the register still shows the correct roles, so the leak is caught.
   A document missing from the register is treated as restricted (fail closed).
2. Sensitivity markers in the text itself (e.g. "STAFF ONLY", "CONFIDENTIAL"), which catch
   restricted content even if the register is also wrong.
3. Support check: every sentence of the answer must be supported by the cited sources
   (word overlap offline; LLM judgement in openai mode).

Decision: pass, revise (drop the offending sources and answer again) or block (neutral reply).
"""
import csv
import json
import re

from .. import config
from ..embeddings import _stem, tokens
from .answerer import split_sentences

MARKERS = {
    "student": ["staff only", "admin only", "confidential", "marking guide", "model answer",
                "do not share", "hr confidential", "watch list"],
    "lecturer": ["admin only", "hr confidential"],
    "admin": [],
}

JUDGE = (
    "You check whether an answer is fully supported by the given sources. "
    'Return JSON: {"supported": true|false, "unsupported_sentences": [..]}.'
)


def load_register(path=config.ROOT / "data" / "access_register.csv"):
    with open(path, newline="", encoding="utf-8") as f:
        return {r["doc_id"]: set(r["allowed_roles"].split(";")) for r in csv.DictReader(f)}


def _support(sentence, chunks):
    s = {_stem(t) for t in tokens(re.sub(r"\[\d+\]", "", sentence))}
    if not s:
        return 1.0
    return max(len(s & {_stem(t) for t in tokens(c["text"])}) / len(s) for c in chunks)


class Verifier:
    def __init__(self, llm=None, register=None):
        self.llm = llm
        self.register = register if register is not None else load_register()

    def run(self, question, role, draft):
        answer, chunks = draft["answer"], draft["citations"]
        result = {"decision": "pass", "reasons": [], "bad_chunks": [], "usage": {}}
        if answer == config.NEUTRAL_REPLY:
            return result

        # 1 + 2: leak checks, independent of the vector-DB tags
        for c in chunks:
            allowed = self.register.get(c["doc_id"])
            if allowed is None:
                result["reasons"].append(f"{c['doc_id']} not in access register")
                result["bad_chunks"].append(c["id"])
            elif role not in allowed:
                result["reasons"].append(f"register: {c['doc_id']} not allowed for {role}")
                result["bad_chunks"].append(c["id"])
            else:
                hit = [m for m in MARKERS[role] if m in c["text"].lower()]
                if hit:
                    result["reasons"].append(f"sensitivity marker {hit} in {c['doc_id']}")
                    result["bad_chunks"].append(c["id"])
        if any(m in answer.lower() for m in MARKERS[role]):
            result["reasons"].append("sensitivity marker in answer text")
            result["decision"] = "block"
            return result
        if result["bad_chunks"]:
            result["decision"] = "revise"
            return result

        # 3: support check
        if self.llm:
            src = "\n".join(f"[{i + 1}] {c['text']}" for i, c in enumerate(chunks))
            text, usage = self.llm.chat(JUDGE, f"Sources:\n{src}\n\nAnswer: {answer}", json_mode=True)
            result["usage"] = usage
            try:
                verdict = json.loads(text)
            except json.JSONDecodeError:
                verdict = {"supported": False, "unsupported_sentences": ["judge output not valid JSON"]}
            if not verdict.get("supported", False):
                result["decision"] = "revise"
                result["reasons"].append(f"unsupported: {verdict.get('unsupported_sentences')}")
        else:
            weak = [s for s in split_sentences(answer) if _support(s, chunks) < 0.6]
            if weak:
                result["decision"] = "revise"
                result["reasons"].append(f"unsupported: {weak}")
        return result
