"""Verifier agent: second layer after role-filtered retrieval.

It does NOT trust the role tags stored in the vector database. It checks the draft answer with
information that is kept separately from the retrieval index:

1. Access register (data/access_register.csv): the list of which roles may see each document,
   maintained by the document owners. If a chunk was tagged wrongly when it was uploaded to the
   vector database, the register still shows the correct roles, so the leak is caught.
   A document missing from the register is treated as restricted (fail closed).
2. Sensitivity markers (e.g. "STAFF ONLY", "CONFIDENTIAL"), which catch restricted content
   even if the register is also wrong. They are checked in the chunk AND in the whole source
   document (read from data/docs, not from the vector DB): a label is usually written once at
   the top, so only the first chunk carries it, and later chunks of the same document would
   otherwise pass (found in testing, v0.11).
3. Relevance check (v1.1): the answer must address the question, not just be copied from a
   source (answer-type and coverage rules offline, see relevance.py; LLM judgement in openai mode).
   Since v1.5 it also checks that every cited source comes from the university the question
   names ("At Heriot-Watt, ..." must not be answered from a UOW policy), in both modes.
4. Support check: every sentence of the answer must be supported by the cited sources
   (word overlap offline; LLM judgement in openai mode).

Leak checks run over every chunk the answerer was shown, not only the ones it cited.

Decision: pass, revise (drop the offending sources and answer again) or block (neutral reply).
"""
import csv
import json
import re

from .. import config
from ..embeddings import _stem, tokens
from .answerer import split_sentences
from .relevance import RelevanceChecker

# Access labels count only in label form (upper case, e.g. "STAFF ONLY", "CONFIDENTIAL"). Before
# v1.2 any "confidential" counted, and 9 of the 16 real public policies use the word in ordinary
# sentences ("a fair and confidential process"), so students lost correct answers (run 6).
LABELS = {
    "student": ["STAFF ONLY", "ADMIN ONLY", "HR CONFIDENTIAL", "CONFIDENTIAL"],
    "lecturer": ["ADMIN ONLY", "HR CONFIDENTIAL"],
    "admin": [],
}
# Phrases that signal restricted content whatever the case (checked in lower case).
PHRASES = {
    "student": ["marking guide", "model answer", "do not share", "watch list"],
    "lecturer": [],
    "admin": [],
}


def find_markers(text, role):
    hits = [lab for lab in LABELS[role] if re.search(rf"\b{lab}\b", text)]
    low = text.lower()
    return hits + [p for p in PHRASES[role] if p in low]

JUDGE = (
    "You check a draft answer to a university question. Decide two things: "
    "(1) supported: every sentence is fully supported by the given sources; "
    "(2) answers_question: the answer actually answers the question that was asked, rather than "
    "giving a related but different fact. "
    'Return JSON: {"supported": true|false, "answers_question": true|false, "unsupported_sentences": [..]}.'
)


REGISTER_FILES = (config.ROOT / "data" / "access_register.csv",
                  config.ROOT / "data" / "real" / "access_register.csv")


def load_register(paths=REGISTER_FILES):
    """Merged access register (mock documents + real public documents)."""
    reg = {}
    for path in [paths] if not isinstance(paths, (list, tuple)) else paths:
        if path.exists():
            with open(path, newline="", encoding="utf-8") as f:
                reg.update({r["doc_id"]: set(r["allowed_roles"].split(";")) for r in csv.DictReader(f)})
    return reg


def load_doc_texts(files=None):
    """Full lower-cased text of every source document, keyed by doc_id (independent of ChromaDB)."""
    files = config.corpus_files() if files is None else files
    return {p.stem: p.read_text(encoding="utf-8") for p in files}  # original case: labels are upper case


def _support(sentence, chunks):
    s = {_stem(t) for t in tokens(re.sub(r"\[\d+\]", "", sentence))}
    if not s:
        return 1.0
    return max(len(s & {_stem(t) for t in tokens(c["text"])}) / len(s) for c in chunks)


UNI_IDS = config.REAL_PREFIXES  # mock and uploaded documents have no university to compare


class Verifier:
    def __init__(self, llm=None, register=None, doc_texts=None):
        self.llm = llm
        self.register = register if register is not None else load_register()
        self.doc_texts = doc_texts if doc_texts is not None else load_doc_texts()
        self.relevance = RelevanceChecker(self.doc_texts)

    def run(self, question, role, draft):
        answer, chunks = draft["answer"], draft["citations"]
        # Leak checks cover every chunk the answerer was shown, cited or not (v1.1).
        seen = {c["id"]: c for c in chunks + draft.get("context", [])}
        # issues: which checks failed ("leak", "relevance", "support"); the orchestrator uses it to
        # decide whether a rewrite counts against the quality-revision budget.
        result = {"decision": "pass", "reasons": [], "bad_chunks": [], "issues": [], "usage": {}}
        if answer == config.NEUTRAL_REPLY:
            return result

        # 1 + 2: leak checks, independent of the vector-DB tags
        for c in seen.values():
            allowed = self.register.get(c["doc_id"])
            if allowed is None:
                result["reasons"].append(f"{c['doc_id']} not in access register")
                result["bad_chunks"].append(c["id"])
            elif role not in allowed:
                result["reasons"].append(f"register: {c['doc_id']} not allowed for {role}")
                result["bad_chunks"].append(c["id"])
            else:
                source = c["text"] + "\n" + self.doc_texts.get(c["doc_id"], "")
                hit = find_markers(source, role)
                if hit:
                    result["reasons"].append(f"sensitivity marker {hit} in {c['doc_id']}")
                    result["bad_chunks"].append(c["id"])
        result["reasons"] = list(dict.fromkeys(result["reasons"]))  # one reason per document
        if find_markers(answer, role):
            result["reasons"].append("sensitivity marker in answer text")
            result["issues"].append("leak")
            result["decision"] = "block"
            return result
        if result["bad_chunks"]:
            result["decision"] = "revise"
            result["issues"].append("leak")
            return result

        # 3a: the sources must come from the university the question is about (v1.5)
        named = {config.canonical_university(u) for u in config.universities_named(question)}
        if named:
            other = [c for c in chunks if config.university_of(c["doc_id"]) in UNI_IDS
                     and config.university_of(c["doc_id"]) not in named]
            if other:
                asked = " / ".join(config.university_label(u)[0] for u in sorted(named))
                for c in other:
                    result["reasons"].append(f"not relevant: question is about {asked}, but the source is from "
                                             f"{config.university_label(config.university_of(c['doc_id']))[0]}")
                result["reasons"] = list(dict.fromkeys(result["reasons"]))
                result["bad_chunks"] += [c["id"] for c in other]
                result["decision"] = "revise"
                result["issues"].append("relevance")
                return result

        # 3 + 4: relevance and support
        if self.llm:
            src = "\n".join(f"[{i + 1}] {c['text']}" for i, c in enumerate(chunks))
            text, usage = self.llm.chat(
                JUDGE, f"Question: {question}\n\nSources:\n{src}\n\nAnswer: {answer}", json_mode=True)
            result["usage"] = usage
            try:
                verdict = json.loads(text)
            except json.JSONDecodeError:
                verdict = {"supported": False, "unsupported_sentences": ["judge output not valid JSON"]}
            # Missing keys count as "no" (fail closed), like a missing register entry.
            if not verdict.get("answers_question", False):
                result["decision"] = "revise"
                result["reasons"].append("not relevant: judge says the answer does not answer the question")
                result["issues"].append("relevance")
            if not verdict.get("supported", False):
                result["decision"] = "revise"
                result["reasons"].append(f"unsupported: {verdict.get('unsupported_sentences')}")
                result["issues"].append("support")
        else:
            irrelevant = self.relevance.check(question, answer)
            if irrelevant:
                # Drop the sources it was built from, so the answerer tries the other chunks.
                result["decision"] = "revise"
                result["reasons"] += [f"not relevant: {r}" for r in irrelevant]
                result["issues"].append("relevance")
                result["bad_chunks"] += [c["id"] for c in chunks]
                return result
            weak = [s for s in split_sentences(answer) if _support(s, chunks) < 0.6]
            if weak:
                result["decision"] = "revise"
                result["issues"].append("support")
                result["reasons"].append(f"unsupported: {weak}")
        return result
