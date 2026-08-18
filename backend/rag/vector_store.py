
import os
from typing import List, Dict
import logging
from backend.rag.embeddings import generate_embeddings
from qdrant_client import QdrantClient, models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QDrantVectorStore:
    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        embedding_model_name: str = "gemini-embedding-001",
        embedding_dimension: int = 768
        ):
        self.qdrant_client = QdrantClient(url=qdrant_url)
        self._collection_ready = False
        self.embedding_model_name = embedding_model_name
        self.embedding_dimension = embedding_dimension
        self.collection_name = "resshare_vectors"

    def _ensure_collection(self) -> bool:
            if self._collection_ready:
                return True

            try:
                if not self.qdrant_client.collection_exists(self.collection_name):
                    self.qdrant_client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=models.VectorParams(
                            size=self.embedding_dimension,
                            distance=models.Distance.COSINE,
                        ),
                    )

                for field_name in ("user_id", "document_id"):
                    self.qdrant_client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name=field_name,
                        field_schema=models.PayloadSchemaType.KEYWORD,
                        wait=True,
                    )

                self._collection_ready = True
                return True
            except Exception as exc:
                logger.error("Failed to initialize Qdrant collection: %s", exc)
                return False

    def add_chunks(self, username: str, chunks: List[Dict]) -> bool:
            """
            Add text chunks to user's vector database
            
            Args:
                username: User identifier
                chunks: List of chunk dictionaries                
            Returns:
                Success boolean
            """
            if not chunks:
                return True
            
            try:
                if not self._ensure_collection():
                    return False

                texts = [chunk["text"] for chunk in chunks]
                logger.info("Preparing to add %s chunks for user '%s'", len(texts), username)
                
                embeddings = generate_embeddings(texts, embedding_model=self.embedding_model_name, embedding_dimensions=self.embedding_dimension, task_type="RETRIEVAL_DOCUMENT")
                if embeddings.size == 0:
                    return False

                #Deleting old chunks for the same document before adding new ones
                document_id = chunks[0]["metadata"]["document_id"]
                if not self.delete_documents(username, [document_id]):
                    return False

                points = []
                for chunk, embedding in zip(chunks, embeddings):
                    metadata = chunk["metadata"]
                    payload = {
                        "user_id": username,
                        "document_id": metadata["document_id"],
                        "cid": metadata["cid"],
                        "filename": metadata["filename"],
                        "path": metadata["path"],
                        "file_type": metadata["file_type"],
                        "chunk_index": metadata["chunk_index"],
                        "chunk_text": chunk["text"],
                        "embedding_model": self.embedding_model_name,
                    }
                    points.append(
                        models.PointStruct(
                            id=metadata["chunk_id"],
                            vector=embedding.tolist(),
                            payload=payload,
                        )
                    )

                logger.debug("Upserting %s vectors into Qdrant", len(points))
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=points,
                    wait=True,
                )
                logger.info(f"Indexed {len(points)} chunks for user '{username}', document '{document_id}'")
                return True

            except Exception as exc:
                logger.error("Failed to add chunks to Qdrant: %s", exc)
                return False

    def search_user_vector_db(self, username: str, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search user's vector database for relevant chunks
        
        Args:
            username: User identifier
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of relevant chunks with scores
        """
        if not self._ensure_collection():
            return []

        try:
            query_embedding = generate_embeddings([query], embedding_model=self.embedding_model_name, embedding_dimensions=self.embedding_dimension, task_type="RETRIEVAL_QUERY")

            if query_embedding.size == 0:
                logger.warning("Query embedding generation failed for user '%s'", username)
                return []

            response = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=query_embedding[0].tolist(),
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=username), #maybe username is not the best identifier, but for now it works
                        )
                    ]
                ),
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )

            results = []
            for point in response.points:
                payload = point.payload or {}
                metadata = {
                    key: payload.get(key)
                    for key in (
                        "user_id",
                        "document_id",
                        "cid",
                        "filename",
                        "path",
                        "file_type",
                        "chunk_index",
                        "embedding_model",
                    )
                }
                results.append(
                    {
                        "chunk": {
                            "text": payload.get("chunk_text", ""),
                            "metadata": metadata,
                        },
                        "score": float(point.score),
                    }
                )

            logger.info(f"Qdrant search returned {len(results)} results")
            return results

        except Exception as exc:
            logger.error("Failed to search Qdrant: %s", exc)
            return []

    def delete_documents(self, username: str, document_ids: List[str]) -> bool:
        """Delete all chunks owned by a user for the supplied document IDs."""
        if not document_ids:
            return True
        if not self._ensure_collection():
            return False

        try:
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="user_id",
                                match=models.MatchValue(value=username),
                            ),
                            models.FieldCondition(
                                key="document_id",
                                match=models.MatchAny(any=document_ids),
                            ),
                        ]
                    )
                ),
                wait=True,
            )
            return True
        except Exception as exc:
            logger.error("Failed to delete documents from Qdrant: %s", exc)
            return False


    def delete_user_data(self, username: str) -> bool:
        """Delete every indexed chunk owned by a user."""
        if not self._ensure_collection():
            return False

        try:
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="user_id",
                                match=models.MatchValue(value=username),
                            )
                        ]
                    )
                ),
                wait=True,
            )
            return True
        except Exception as exc:
            logger.error("Failed to delete user data from Qdrant: %s", exc)
            return False

def get_vector_store(qdrant_url: str = "") -> QDrantVectorStore:
    """
    Factory function to get a QDrantVectorStore instance
    
    Args:
        qdrant_url: URL of the Qdrant service
        
    Returns:
        QDrantVectorStore instance
    """
    if not qdrant_url:
        qdrant_url = os.getenv("QDRANT_VECTOR_DB_URL", "http://localhost:6333")
    return QDrantVectorStore(qdrant_url=qdrant_url)