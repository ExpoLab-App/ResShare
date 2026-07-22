import numpy as np
from backend.rag.types import GeminiClientConfig
from typing import List
import requests

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_embeddings(
        texts: List[str],
        embedding_model: str,
        embedding_dimensions: int = 768,
        task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> np.ndarray:
        """
        Generate embeddings for a list of texts using Gemini API batch processing
        
        Args:
            texts: List of text chunks
            
        Returns:
            Numpy array of embeddings
        """
        if not texts:
            return np.array([])
        
        logger.debug(f"Generating embeddings for {len(texts)} texts")
        
        try:
            logger.info(f"Using Gemini API with model: {embedding_model}, dimension: {embedding_dimensions}")
            embedding_url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{embedding_model}:batchEmbedContents"
            )
            client = GeminiClientConfig(model_name=embedding_model, url=embedding_url)
            embeddings = client.get_embeddings(texts, task_type=task_type, dim=embedding_dimensions)
            return embeddings
        
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
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return np.array([])