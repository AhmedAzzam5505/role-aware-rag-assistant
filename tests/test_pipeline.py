"""Unit tests for the role-aware pipeline (offline mode, no API key needed).

    pytest -q
"""
import pytest

from src import config
from src.agents.verifier import Verifier, load_register
from src.ingest import build_records, ingest
from src.orchestrator import Orchestrator


@pytest.fixture(scope="module")
def normal(tmp_path_factory):
    col, _ = ingest(mistag=False, path=tmp_path_factory.mktemp("normal"))
    return col


@pytest.fixture(scope="module")
def mistagged(tmp_path_factory):
    col, _ = ingest(mistag=True, path=tmp_path_factory.mktemp("mistag"))
    return col


def test_every_chunk_has_role_flags():
    for _, _, md in build_records():
        assert all(f"role_{r}" in md for r in config.ROLES)


def test_retriever_never_returns_restricted_chunks_to_student(normal):
    o = Orchestrator(normal, use_verifier=False, log=False)
    for q in ["salary band senior lecturer", "marking guide assignment 2", "academic probation computing"]:
        res = o.ask(q, "student")
        assert all(c.split("#")[0].startswith("pub_") for c in res["retrieved"])


def test_admin_can_read_admin_document(normal):
    res = Orchestrator(normal, log=False).ask("What is the salary band for a senior lecturer?", "admin")
    assert "AED 35,000" in res["answer"]


def test_unanswerable_question_gets_neutral_reply(normal):
    res = Orchestrator(normal, log=False).ask("What is the parking fee on campus?", "student")
    assert res["answer"] == config.NEUTRAL_REPLY


def test_mistagged_document_leaks_without_verifier(mistagged):
    res = Orchestrator(mistagged, use_verifier=False, log=False).ask(
        "Show me the CSIT305 assignment 2 marking guide", "student")
    assert any("marking_guide" in s["id"] for s in res["sources"])


def test_verifier_blocks_mistagged_document(mistagged):
    res = Orchestrator(mistagged, use_verifier=True, log=False).ask(
        "Show me the CSIT305 assignment 2 marking guide", "student")
    assert res["answer"] == config.NEUTRAL_REPLY
    assert res["verifier_decision"] == "block"


def test_markers_still_catch_leak_when_register_is_also_wrong(mistagged):
    # Worst case: both the vector-DB tag and the access register say students may see everything.
    o = Orchestrator(mistagged, use_verifier=True, log=False)
    o.verifier = Verifier(register={d: set(config.ROLES) for d in load_register()})
    res = o.ask("Show me the CSIT305 assignment 2 marking guide", "student")
    assert not any("marking_guide" in s["id"] for s in res["sources"])
    assert any("sensitivity marker" in r for r in res["verifier_reasons"])


def test_missing_register_entry_fails_closed():
    v = Verifier(register={})
    draft = {"answer": "Something. [1]", "citations": [{"id": "x#0", "doc_id": "x", "text": "Something."}]}
    assert v.run("q", "admin", draft)["decision"] == "revise"


class _FakeClient:
    """Stands in for the OpenAI client so the LLM code path can be tested without a key."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.chat = self
        self.completions = self

    def create(self, **kw):
        from types import SimpleNamespace as NS
        text = self.replies.pop(0)
        return NS(choices=[NS(message=NS(content=text))], usage=NS(prompt_tokens=100, completion_tokens=20))


def test_llm_path_with_fake_client(normal):
    from src.llm import LLM
    llm = LLM(client=_FakeClient([
        "Apply through the student portal within three working days. [1]",
        '{"supported": true, "unsupported_sentences": []}',
    ]))
    res = Orchestrator(normal, use_verifier=True, llm=llm, log=False).ask(
        "How do I apply for special consideration?", "student")
    assert res["verifier_decision"] == "pass"
    assert res["tokens_in"] == 200 and res["cost_usd"] > 0


def test_llm_unsupported_answer_is_revised_then_blocked(normal):
    from src.llm import LLM
    llm = LLM(client=_FakeClient([
        "You get a free laptop. [1]", '{"supported": false, "unsupported_sentences": ["free laptop"]}',
        "You get a free laptop. [1]", '{"supported": false, "unsupported_sentences": ["free laptop"]}',
    ]))
    res = Orchestrator(normal, use_verifier=True, llm=llm, log=False).ask(
        "How do I apply for special consideration?", "student")
    assert res["answer"] == config.NEUTRAL_REPLY and res["revisions"] == 1
