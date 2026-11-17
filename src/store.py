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
        # A wide search beam makes HNSW search effectively exact for our corpus sizes. With the
        # default beam, rebuilding the 1,258-chunk real index changed the top 4 for some questions,
        # so Version A gave different results on identical indexes (run 6).
        configuration={"hnsw": {"space": "cosine", "ef_search": 2000, "ef_construction": 400}},
    )
