import numpy as np
from backend.rag.types import GeminiClientConfig
from typing import List, Dict, Any
import requests
import traceback
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiEmbeddingClient:
    def __init__(self, embedding_model: str, embedding_dimensions: int = 768):
        self.config = GeminiClientConfig(model_name=embedding_model)
        self.embedding_url = (
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{self.config.model_name}:batchEmbedContents"
                )
        self.dims = embedding_dimensions

    def generate_document_embeddings(self, texts: List[str]) -> np.ndarray:
        return self.generate_embeddings(texts, task_type="RETRIEVAL_DOCUMENT")

    def generate_query_embeddings(self, query: List[str]) -> np.ndarray:
        return self.generate_embeddings(query, task_type="RETRIEVAL_QUERY")
   
    def generate_embeddings(
            self,
            texts: List[str],          
            task_type: str = "RETRIEVAL_DOCUMENT"
        ) -> np.ndarray:
            """
            Generate embeddings for a list of texts using Gemini API batch processing
            
            Args:
                texts: List of text chunks
                task_type: Retrieval Query or Indexing docs (https://ai.google.dev/gemini-api/docs/embeddings#task-types-embeddings-1)
            Returns:
                Numpy array of embeddings
            """
            if not texts:
                return np.array([])
                        
            try:
                headers = self._build_headers()
                data = self._build_request_body(texts, task_type)
                
                response = requests.post(self.embedding_url, headers=headers, json=data, timeout=30)
                response.raise_for_status()
                result = response.json()

                embeddings_np = self._get_numpy_embeddings(result.get("embeddings", []))
                logger.debug(f"Built embeddings array with shape {embeddings_np.shape}")

                if len(embeddings_np) != len(texts):
                    logger.warning(f"Mismatch: expected {len(texts)} embeddings, got {len(embeddings_np)}")
                    return np.array([])

                return embeddings_np
            
            except requests.exceptions.Timeout:
                logger.error("Gemini API timeout during batch embedding generation")
                return np.array([])
            except requests.exceptions.RequestException as e:
                logger.error(f"Gemini API request failed: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Response status: {e.response.status_code}")
                    logger.error(f"Response body: {e.response.text}")
                return np.array([])
            except Exception as e:
                logger.error(f"Failed to generate embeddings with Gemini API: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return np.array([])

    def _build_headers(self) -> Dict:
        return {
            "x-goog-api-key": self.config.api_key,
            "Content-Type": "application/json"
        }

    def _build_request_body(self, texts: List[str], task_type: str) -> Dict[str, Any]:
        requests_data = []
        for text in texts:
            requests_data.append({
                "model": f"models/{self.config.model_name}",
                "content": {
                    "parts": [{"text": text}]
                },
                "task_type": task_type,
                "output_dimensionality": self.dims #check best default
            })
        
        return {"requests": requests_data}

    @staticmethod
    def _get_numpy_embeddings(api_embeddings: Dict[str, Any]) -> np.ndarray:
        embeddings = []
        for embedding_response in api_embeddings:
            embedding_values = np.array(embedding_response["values"])
            # if embedding_client.embedding_dimension < 3072:  # Normalize truncated dimensions
            #     norm = np.linalg.norm(embedding_values)
            #     if norm > 0:
            #         embedding_values = embedding_values / norm
            embeddings.append(embedding_values)
        
        embeddings_np = np.array(embeddings)
        logger.debug(f"Built embeddings array with shape {embeddings_np.shape}")
        return embeddings_np