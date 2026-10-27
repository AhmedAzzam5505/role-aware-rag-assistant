"""Embedding functions.

HashingEmbedding works fully offline (no model download) so the prototype runs anywhere.
OpenAIEmbedding is used when an API key is available.
"""
import hashlib
import math
import re

from . import config

STOPWORDS = set("""a an the and or of to in on for is are be by with what when how do does i my me
can you your it this that from at as if will which who where there their they we our us about
please tell show any all have has was were not no""".split())

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS]


def _stem(t: str) -> str:
    for suf in ("ing", "ions", "ion", "es", "s", "ed"):
        if len(t) > len(suf) + 3 and t.endswith(suf):
            return t[: -len(suf)]
    return t


class HashingEmbedding:
    """Bag of stemmed words and bigrams hashed into a fixed-size vector."""

    def __init__(self, dim: int = 1024):
        self.dim = dim

    def name(self) -> str:  # required by chromadb
        return "hashing-embedding"

    def _vec(self, text: str) -> list[float]:
        toks = [_stem(t) for t in tokens(text)]
        feats = toks + [a + "_" + b for a, b in zip(toks, toks[1:])]
        v = [0.0] * self.dim
        for f in feats:
            h = int(hashlib.md5(f.encode()).hexdigest(), 16)
            v[h % self.dim] += 1.0 if "_" not in f else 0.5
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    def __call__(self, input):  # chromadb EmbeddingFunction interface
        return [self._vec(t) for t in input]

    def embed_query(self, input):
        return self(input)

    def embed_documents(self, input):
        return self(input)

    def is_legacy(self):
        return False


class OpenAIEmbedding:
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI()

    def name(self) -> str:
        return "openai-" + config.EMBED_MODEL

    def __call__(self, input):
        out = self.client.embeddings.create(model=config.EMBED_MODEL, input=list(input))
        return [d.embedding for d in out.data]

    def embed_query(self, input):
        return self(input)

    def embed_documents(self, input):
        return self(input)

    def is_legacy(self):
        return False


def get_embedding():
    return OpenAIEmbedding() if config.MODE == "openai" else HashingEmbedding()
