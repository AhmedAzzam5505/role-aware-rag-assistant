"""Thin wrapper around an OpenAI-compatible chat API, with token and cost tracking."""
from . import config


class LLM:
    def __init__(self, client=None):
        if client is None:
            from openai import OpenAI
            client = OpenAI()
        self.client = client

    def chat(self, system: str, user: str, json_mode=False):
        kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
        r = self.client.chat.completions.create(
            model=config.LLM_MODEL,
            temperature=0,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            **kwargs,
        )
        u = r.usage
        usage = {"tokens_in": u.prompt_tokens, "tokens_out": u.completion_tokens,
                 "cost_usd": (u.prompt_tokens * config.PRICE_IN + u.completion_tokens * config.PRICE_OUT) / 1e6}
        return r.choices[0].message.content.strip(), usage
