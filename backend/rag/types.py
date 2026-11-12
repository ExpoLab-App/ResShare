from typing import Optional
import logging
from backend.rag.config import EMBEDDING_MODEL, collection_name

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class RAGProcessResult:
    def __init__(
        self,
        success: bool,
        chunk_count: int = 0,
        embedding_model_name: str = EMBEDDING_MODEL,
        error: Optional[str] = None,
        
    ):
        self.embedding_collection = collection_name()
        self.success = success
        self.chunk_count = chunk_count
        self.error = error
        self.embedding_model_name = embedding_model_name
