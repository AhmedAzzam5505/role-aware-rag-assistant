"""ChromaDB vector store helpers."""
import chromadb

from . import config
from .embeddings import get_embedding


def get_collection(path=None, reset=False):
    client = chromadb.PersistentClient(path=str(path or config.CHROMA_DIR))
    if reset:
        try:
            client.delete_collection(config.COLLECTION)
        except Exception:
            pass
    return client.get_or_create_collection(
        config.COLLECTION,
        embedding_function=get_embedding(),
        metadata={"hnsw:space": "cosine"},
    )
