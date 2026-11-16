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
    for suf in ("ments", "ment", "ing", "ions", "ion", "led", "es", "s", "ed"):
        if len(t) > len(suf) + 3 and t.endswith(suf):
            return t[: -len(suf)]
    return t


class HashingEmbedding:
    """Bag of stemmed words and bigrams hashed into a fixed-size vector."""

    def __init__(self, dim: int = 1024):
        self.dim = dim

    @staticmethod
    def name() -> str:  # required by chromadb
        return "hashing-embedding"

    def get_config(self):
        return {"dim": self.dim}

    @staticmethod
    def build_from_config(cfg):
        return HashingEmbedding(cfg.get("dim", 1024))

    def features(self, text: str) -> list[str]:
        toks = [_stem(t) for t in tokens(text)]
        return toks + [a + "_" + b for a, b in zip(toks, toks[1:])]

    def dim_of(self, feature: str) -> int:
        return int(hashlib.md5(feature.encode()).hexdigest(), 16) % self.dim

    def _vec(self, text: str) -> list[float]:
        v = [0.0] * self.dim
        for f in self.features(text):
            v[self.dim_of(f)] += 1.0 if "_" not in f else 0.5
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    def explain(self, text: str, top: int = 12):
        """What the vector is made of: each feature (stemmed word or bigram), its dimension and its
        weight after normalisation, strongest first. Used by the document explorer in the web page."""
        vec = self._vec(text)
        seen, out = set(), []
        for f in self.features(text):
            d = self.dim_of(f)
            if f not in seen:
                seen.add(f)
                out.append({"feature": f, "dim": d, "weight": round(vec[d], 4)})
        out.sort(key=lambda x: -x["weight"])
        return out[:top]

    def __call__(self, input):  # chromadb EmbeddingFunction interface
        return [self._vec(t) for t in input]

    def embed_query(self, input):
        return self(input)

    def embed_documents(self, input):
        return self(input)

    def supported_spaces(self):  # chromadb >= 1.0 asks every embedding function for this
        return ["cosine", "l2", "ip"]

    def default_space(self):
        return "cosine"

    def is_legacy(self):
        return False


class OpenAIEmbedding:
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI()

    @staticmethod
    def name() -> str:
        return "openai-" + config.EMBED_MODEL

    def get_config(self):
        return {"model": config.EMBED_MODEL}

    @staticmethod
    def build_from_config(cfg):
        return OpenAIEmbedding()

    def __call__(self, input):
        out = self.client.embeddings.create(model=config.EMBED_MODEL, input=list(input))
        return [d.embedding for d in out.data]

    def embed_query(self, input):
        return self(input)

    def embed_documents(self, input):
        return self(input)

    def supported_spaces(self):  # chromadb >= 1.0 asks every embedding function for this
        return ["cosine", "l2", "ip"]

    def default_space(self):
        return "cosine"

    def is_legacy(self):
        return False


def get_embedding():
    return OpenAIEmbedding() if config.MODE == "openai" else HashingEmbedding()
