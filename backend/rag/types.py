from typing import Optional
import requests
import logging
import os
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class RAGProcessResult:
    def __init__(
        self,
        success: bool,
        chunk_count: int = 0,
        embedding_model_name: str = "gemini-embedding-001",
        error: Optional[str] = None,
        
    ):
        self.success = success
        self.chunk_count = chunk_count
        self.error = error
        self.embedding_model_name = embedding_model_name

class GeminiClientConfig:
    def __init__(self, url: str, model_name: str = "gemini-embedding-001"):
        self.api_key = self._load_api_key()
        self.model_name = model_name
        self.url = url

    def get_text_response(self, prompt: str, max_tokens: int) -> str:
        """Generate response using Gemini API"""
        try:
            headers = {
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json"
            }

            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "maxOutputTokens": max_tokens
                },
                "systemInstruction": {
                    "parts": [
                        {
                            "text": "You are a helpful assistant that answers questions based on the provided context from user's documents."
                        }
                    ]
                }
            }

            response = requests.post(self.url, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()
            logger.debug(f"Gemini API response: {result}")
            return result['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    def get_embeddings(self, texts: list, task_type: str = "RETRIEVAL_DOCUMENT", dim: int = 768) -> np.ndarray:
        """Check if Gemini API is reachable and the API key is valid"""

        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        requests_data = []
        for text in texts:
            requests_data.append({
                "model": f"models/{self.model_name}",
                "content": {
                    "parts": [{"text": text}]
                },
                "task_type": task_type, #Figure out what's the point of adding task_type?
                "output_dimensionality": dim
            })
        
        data = {"requests": requests_data}
        
        logger.info(f"Embedding request payload count: {len(requests_data)}")
        response = requests.post(self.url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Embedding API responded with keys: {list(result.keys())}")
                    
        embeddings = []
        api_embeddings = result.get("embeddings", [])
        logger.info(f"Embedding objects returned: {len(api_embeddings)}")
        for embedding_response in api_embeddings:
            embedding_values = np.array(embedding_response["values"])
            # if embedding_client.embedding_dimension < 3072:  # Normalize truncated dimensions
            #     norm = np.linalg.norm(embedding_values)
            #     if norm > 0:
            #         embedding_values = embedding_values / norm
            embeddings.append(embedding_values)
        
        if len(embeddings) != len(texts):
            logger.info(f"Mismatch: expected {len(texts)} embeddings, got {len(embeddings)}")
            return np.array([])
        
        embeddings_np = np.array(embeddings)
        logger.debug(f"Built embeddings array with shape {embeddings_np.shape}")
        return embeddings_np

    def _load_api_key(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("GOOGLE_API_KEY not found in environment variables")
        return api_key