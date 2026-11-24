"""Claude drop-in for src/llm.LLM: same chat(system, user, json_mode) -> (text, usage) interface.

Used by the answerer (free text) and the verifier's judge (JSON).
"""
import json
import threading
import time

import anthropic

MODEL = "claude-opus-5-5"
PRICE_IN, PRICE_OUT = 4.00, 20.00  # USD per 1M tokens (claude-opus-5-5)
EFFORT = "low"  # short reading-comprehension calls; thinking cannot be switched off on this model

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "supported": {"type": "boolean"},
        "answers_question": {"type": "boolean"},
        "unsupported_sentences": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["supported", "answers_question", "unsupported_sentences"],
    "additionalProperties": False,
}
FAIL_CLOSED = json.dumps({"supported": False, "answers_question": False,
                          "unsupported_sentences": ["judge refused or returned no JSON"]})


class BudgetExceeded(RuntimeError):
    pass


class ClaudeLLM:
    def __init__(self, neutral_reply, budget_usd, log_path, client=None):
        self.client = client or anthropic.Anthropic(max_retries=6)
        self.neutral = neutral_reply
        self.budget = budget_usd
        self.spent = 0.0
        self.calls = 0
        self.refusals = 0
        self.log = open(log_path, "a")
        self.lock = threading.Lock()

    def chat(self, system: str, user: str, json_mode=False):
        if self.spent >= self.budget:
            raise BudgetExceeded(f"budget ${self.budget:.2f} reached (spent ${self.spent:.2f})")
        output_config = {"effort": EFFORT}
        if json_mode:
            output_config["format"] = {"type": "json_schema", "schema": JUDGE_SCHEMA}
        t0 = time.perf_counter()
        r = self.client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config=output_config,
            # Server-side refusal fallback (on by default for this model in our setup).
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        dt = time.perf_counter() - t0
        u = r.usage
        tin = (u.input_tokens or 0) + (getattr(u, "cache_read_input_tokens", 0) or 0) + \
              (getattr(u, "cache_creation_input_tokens", 0) or 0)
        tout = u.output_tokens or 0
        cost = (tin * PRICE_IN + tout * PRICE_OUT) / 1e6
        text = "".join(b.text for b in r.content if b.type == "text").strip()
        refused = r.stop_reason == "refusal"
        if refused or not text:
            # Fail closed: the answerer gives the neutral reply, the judge says "not supported".
            text = FAIL_CLOSED if json_mode else self.neutral
        with self.lock:
            self.spent += cost
            self.calls += 1
            self.refusals += refused
            self.log.write(json.dumps({"t": round(dt, 3), "json": json_mode, "in": tin, "out": tout,
                                       "cost": round(cost, 6), "stop": r.stop_reason, "model": r.model,
                                       "request_id": getattr(r, "_request_id", None)}) + "\n")
            self.log.flush()
        return text, {"tokens_in": tin, "tokens_out": tout, "cost_usd": cost}
