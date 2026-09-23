from backend.rag.types import RAGProcessResult
from backend.rag.extraction import extract_text_from_file
from backend.rag.chunking import chunk_text
from backend.rag.vector_store import get_vector_store

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_file_for_rag(
        file_content: bytes,
        filename: str,
        username: str,
        cid: str,
        document_id: str,
        path: str,
    ) -> RAGProcessResult:
        """
        Complete pipeline to process a file for RAG
        
        Args:
            file_content: Raw file bytes
            filename: Name of the file
            username: User who uploaded the file
            cid: IPFS CID of the file
            document_id: Stable uploaded-document identifier
            path: Current user-visible file path
            
        Returns:
            Processing result including chunk count and error details
        """
        try:
            
            #surely there is a better way to do this than creating a new instance every time
            vector_store = get_vector_store()

            text = extract_text_from_file(file_content, filename)
            if not text.strip():
                logger.info(f"No text extracted from {filename}")
                return RAGProcessResult(False, error="No extractable text found", embedding_model_name=vector_store.embedding_model_name)

            metadata = {
                "user_id": username,
                "document_id": document_id,
                "filename": filename,
                "cid": cid,
                "path": path,
                "file_type": filename.lower().split('.')[-1],
            }

            chunks = chunk_text(text, metadata)
            if not chunks:
                logger.info(f"No chunks created from {filename}")
                return RAGProcessResult(False, error="No text chunks were created", embedding_model_name=vector_store.embedding_model_name)

            
            success = vector_store.add_chunks(username, chunks)
            if success:
                logger.info(f"Successfully processed {filename} for RAG: {len(chunks)} chunks")
                return RAGProcessResult(True, chunk_count=len(chunks), embedding_model_name=vector_store.embedding_model_name)

            return RAGProcessResult(
                False,
                error="Embedding generation or Qdrant indexing failed",
                embedding_model_name=vector_store.embedding_model_name,
            )

        except Exception as exc:
            logger.error("Failed to process file for RAG: %s", exc)
            return RAGProcessResult(False, error=str(exc))