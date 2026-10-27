"""Retriever agent: searches ONLY the chunks the user's role may see.

The role filter is applied inside the vector search (metadata `where` clause), so restricted
chunks are removed before ranking and never reach the answerer or the LLM.
"""
from .. import config


class Retriever:
    def __init__(self, collection):
        self.col = collection

    def run(self, question: str, role: str, k: int = config.TOP_K):
        if role not in config.ROLES:
            raise ValueError(f"unknown role: {role}")
        res = self.col.query(query_texts=[question], n_results=k, where={f"role_{role}": True})
        chunks = []
        for cid, text, md, dist in zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]):
            chunks.append({"id": cid, "text": text, "score": round(1 - dist, 3), **md})
        return chunks
