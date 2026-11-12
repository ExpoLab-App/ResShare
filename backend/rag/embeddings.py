"""Cached local FastEmbed encoder with separate passage and query methods."""
from functools import lru_cache
import os

import numpy as np

from backend.rag.config import EMBEDDING_DIMENSION, EMBEDDING_MODEL


@lru_cache(maxsize=1)
def get_embedding_model(model_name, cache_dir):
    from fastembed import TextEmbedding
    return TextEmbedding(model_name=model_name, cache_dir=cache_dir)


class LocalEmbeddingClient:
    def __init__(self, embedding_model=EMBEDDING_MODEL, embedding_dimensions=EMBEDDING_DIMENSION):
        if embedding_model != EMBEDDING_MODEL or embedding_dimensions != EMBEDDING_DIMENSION:
            raise ValueError("This embedding pipeline requires BGE small en v1.5 with 384 dimensions")
        self.model_name = embedding_model
        self.dims = embedding_dimensions

    def _embed(self, texts, query=False):
        if not texts:
            return np.empty((0, self.dims), dtype=np.float32)
        model = get_embedding_model(self.model_name, os.getenv("FASTEMBED_CACHE_PATH"))
        vectors = model.query_embed(texts) if query else model.passage_embed(texts)
        result = np.asarray(list(vectors), dtype=np.float32)
        if result.shape != (len(texts), self.dims) or not np.isfinite(result).all():
            raise ValueError("Embedding model returned invalid vectors")
        if np.any(np.linalg.norm(result, axis=1) == 0):
            raise ValueError("Embedding model returned zero vectors")
        return result

    def generate_document_embeddings(self, texts):
        return self._embed(texts)

    def generate_query_embeddings(self, texts):
        return self._embed(texts, query=True)
