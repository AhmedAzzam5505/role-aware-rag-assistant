"""Orchestrator: runs retriever -> answerer -> verifier in order.

Version A = role filter only (use_verifier=False).
Version B = role filter + verifier (use_verifier=True).
"""
import time

from . import config
from .agents.answerer import Answerer
from .agents.retriever import Retriever
from .agents.verifier import Verifier
from .logger import log_query
from .store import get_collection

MAX_REVISIONS = 1


class Orchestrator:
    def __init__(self, collection=None, use_verifier=True, llm=None, log=True):
        if llm is None and config.MODE == "openai":
            from .llm import LLM
            llm = LLM()
        self.retriever = Retriever(collection or get_collection())
        self.answerer = Answerer(llm)
        self.verifier = Verifier(llm) if use_verifier else None
        self.version = "B" if use_verifier else "A"
        self.log = log

    def ask(self, question, role):
        t0 = time.perf_counter()
        chunks = self.retriever.run(question, role)
        draft = self.answerer.run(question, chunks)
        usage = [draft["usage"]]
        decision, reasons, revisions = "none", [], 0

        if self.verifier:
            v = self.verifier.run(question, role, draft)
            usage.append(v["usage"])
            decision, reasons = v["decision"], list(v["reasons"])
            while decision == "revise" and revisions < MAX_REVISIONS:
                revisions += 1
                chunks = [c for c in chunks if c["id"] not in v["bad_chunks"]]
                draft = self.answerer.run(question, chunks, feedback="; ".join(v["reasons"]))
                usage.append(draft["usage"])
                v = self.verifier.run(question, role, draft)
                usage.append(v["usage"])
                decision = v["decision"]
                reasons += v["reasons"]
            if decision in ("revise", "block"):
                decision = "block"
                draft = {"answer": config.NEUTRAL_REPLY, "citations": []}

        out = {
            "version": self.version,
            "role": role,
            "question": question,
            "answer": draft["answer"],
            "sources": [{"id": c["id"], "title": c["title"]} for c in draft["citations"]],
            "retrieved": [c["id"] for c in chunks],
            "verifier_decision": decision,
            "verifier_reasons": reasons,
            "revisions": revisions,
            "latency_s": round(time.perf_counter() - t0, 4),
            "tokens_in": sum(u.get("tokens_in", 0) for u in usage),
            "tokens_out": sum(u.get("tokens_out", 0) for u in usage),
            "cost_usd": round(sum(u.get("cost_usd", 0.0) for u in usage), 6),
            "mode": config.MODE,
        }
        if self.log:
            log_query(out)
        return out
