"""ChromaDB vector store helpers."""
import chromadb

from . import config
from .embeddings import get_embedding


def get_collection(path=None, reset=False):
    client = chromadb.PersistentClient(path=str(path or config.CHROMA_DIR))
    # One collection per corpus, so switching RAG_CORPUS never mixes the two document sets.
    name = config.COLLECTION if config.CORPUS == "mock" else f"{config.COLLECTION}_{config.CORPUS}"
    if reset:
        try:
            client.delete_collection(name)
        except Exception:
            pass
    return client.get_or_create_collection(
        name,
        embedding_function=get_embedding(),
        metadata={"hnsw:space": "cosine"},
    )
