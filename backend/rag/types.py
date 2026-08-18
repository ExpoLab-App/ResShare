from typing import Optional
import logging
import os

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
    def __init__(self, model_name: str = "gemini-embedding-001"):
        self.api_key = self._load_api_key()
        self.model_name = model_name

    def _load_api_key(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("GOOGLE_API_KEY not found in environment variables")
        return api_key