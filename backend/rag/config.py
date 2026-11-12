"""Local RAG defaults. A new embedding space always needs a new collection."""
import os

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIMENSION = 384
DEFAULT_COLLECTION = "resshare_bge_small_en_v15_v1"


def collection_name():
    name = os.getenv("RAG_COLLECTION", DEFAULT_COLLECTION)
    if not name or name == "resshare_vectors":
        raise ValueError("Local embeddings require a separate RAG_COLLECTION")
    return name
