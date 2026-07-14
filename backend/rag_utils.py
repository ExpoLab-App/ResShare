import os
from dataclasses import dataclass
from io import BytesIO
import logging
from typing import Dict, List, Optional
from uuid import NAMESPACE_URL, uuid5

import numpy as np
import PyPDF2
from docx import Document
from langchain.docstore.document import Document as LangchainDocument
from langchain.text_splitter import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient, models
import requests


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RAGProcessResult:
    success: bool
    chunk_count: int = 0
    error: Optional[str] = None


class RAGManager:
    """
    Manages RAG (Retrieval-Augmented Generation) functionality for the file sharing app.
    Handles text extraction, chunking, embeddings, and vector search.
    """
    
    COLLECTION_NAME = "document_chunks_v1"

    def __init__(
        self,
        embedding_model: str = "gemini-embedding-001",
        embedding_dimension: int = 768,
        qdrant_client: Optional[QdrantClient] = None,
    ):
        """
        Initialize RAG Manager
        
        Args:
            embedding_model: Gemini embedding model name
            embedding_dimension: Output embedding dimension (768, 1536, or 3072)
            qdrant_client: Optional client override used by tests
        """
        self.embedding_model_name = embedding_model
        self.embedding_dimension = embedding_dimension
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self._collection_ready = False
        self.qdrant_client = qdrant_client or QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
            timeout=10,
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        
        self._setup_gemini_api()

    def _ensure_collection(self) -> bool:
        if self._collection_ready:
            return True

        try:
            if not self.qdrant_client.collection_exists(self.COLLECTION_NAME):
                self.qdrant_client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=models.VectorParams(
                        size=self.embedding_dimension,
                        distance=models.Distance.COSINE,
                    ),
                )

            for field_name in ("user_id", "document_id"):
                self.qdrant_client.create_payload_index(
                    collection_name=self.COLLECTION_NAME,
                    field_name=field_name,
                    field_schema=models.PayloadSchemaType.KEYWORD,
                    wait=True,
                )

            self._collection_ready = True
            return True
        except Exception as exc:
            logger.error("Failed to initialize Qdrant collection: %s", exc)
            return False
    
    def _setup_gemini_api(self):
        """Setup Gemini API configuration (no client needed for REST API)"""
        api_key = self.api_key
        if not api_key:
            logger.warning("GOOGLE_API_KEY not found in environment variables")
        return api_key is not None
    
    def extract_text_from_file(self, file_content: bytes, filename: str) -> str:
        """
        Extract text from various file formats
        
        Args:
            file_content: Raw bytes of the file
            filename: Name of the file (used to determine format)
            
        Returns:
            Extracted text content
        """
        file_extension = filename.lower().split('.')[-1]
        
        try:
            if file_extension == 'pdf':
                return self._extract_from_pdf(file_content)
            elif file_extension == 'docx':
                return self._extract_from_docx(file_content)
            elif file_extension == 'txt':
                return self._extract_from_txt(file_content)
            else:
                logger.warning(f"Unsupported file type: {file_extension}")
                return ""
        except Exception as e:
            logger.error(f"Failed to extract text from {filename}: {e}")
            return ""
    
    def _extract_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
        return text.strip()
    
    def _extract_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file"""
        text = ""
        try:
            doc = Document(BytesIO(file_content))
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            logger.error(f"DOCX extraction error: {e}")
        return text.strip()
    
    def _extract_from_txt(self, file_content: bytes) -> str:
        """Extract text from TXT file"""
        try:
            return file_content.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"TXT extraction error: {e}")
            return ""
    
    def chunk_text(self, text: str, metadata: Dict) -> List[Dict]:
        """
        Split text into chunks with metadata
        
        Args:
            text: Text to chunk
            metadata: Metadata to attach to each chunk
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        if not text.strip():
            return []
        
        doc = LangchainDocument(page_content=text, metadata=metadata)
        
        chunks = self.text_splitter.split_documents([doc])
        
        chunk_dicts = []
        for i, chunk in enumerate(chunks):
            chunk_dict = {
                'text': chunk.page_content,
                'metadata': {
                    **chunk.metadata,
                    'chunk_index': i,
                    'chunk_id': str(uuid5(
                        NAMESPACE_URL,
                        (
                            f"reshare:{metadata['document_id']}:"
                        ),
                    ))
                }
            }
            chunk_dicts.append(chunk_dict)
        
        return chunk_dicts
    
    def generate_embeddings(
        self,
        texts: List[str],
        task_type: str = "RETRIEVAL_DOCUMENT",
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
        
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        api_key = self.api_key
        if not api_key:
            logger.error("GOOGLE_API_KEY not found in environment variables")
            return np.array([])
        
        logger.info(f"Using Gemini API with model: {self.embedding_model_name}, dimension: {self.embedding_dimension}")
        
        try:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{self.embedding_model_name}:batchEmbedContents"
            )
            
            headers = {
                "x-goog-api-key": api_key,
                "Content-Type": "application/json"
            }
            
            requests_data = []
            for text in texts:
                requests_data.append({
                    "model": f"models/{self.embedding_model_name}",
                    "content": {
                        "parts": [{"text": text}]
                    },
                    "task_type": task_type,
                    "output_dimensionality": self.embedding_dimension
                })
            
            data = {"requests": requests_data}
            
            logger.info(f"Embedding request payload count: {len(requests_data)}")
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Embedding API responded with keys: {list(result.keys())}")
            
            embeddings = []
            api_embeddings = result.get("embeddings", [])
            logger.info(f"Embedding objects returned: {len(api_embeddings)}")
            for embedding_response in api_embeddings:
                embedding_values = np.array(embedding_response["values"])
                if self.embedding_dimension < 3072:  # Normalize truncated dimensions
                    norm = np.linalg.norm(embedding_values)
                    if norm > 0:
                        embedding_values = embedding_values / norm
                embeddings.append(embedding_values)
            
            if len(embeddings) != len(texts):
                logger.info(f"Mismatch: expected {len(texts)} embeddings, got {len(embeddings)}")
                return np.array([])
            
            embeddings_np = np.array(embeddings)
            logger.info(f"Built embeddings array with shape {embeddings_np.shape}")
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
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return np.array([])
    
    def add_chunks_to_vector_db(self, username: str, chunks: List[Dict]) -> bool:
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

            embeddings = self.generate_embeddings(texts)
            if embeddings.size == 0:
                return False

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
                collection_name=self.COLLECTION_NAME,
                points=points,
                wait=True,
            )
            logger.info(
                "Indexed %s chunks for user '%s', document '%s'",
                len(points),
                username,
                document_id,
            )
            return True

        except Exception as exc:
            logger.error("Failed to add chunks to Qdrant: %s", exc)
            return False

    def delete_documents(self, username: str, document_ids: List[str]) -> bool:
        """Delete all chunks owned by a user for the supplied document IDs."""
        if not document_ids:
            return True
        if not self._ensure_collection():
            return False

        try:
            self.qdrant_client.delete(
                collection_name=self.COLLECTION_NAME,
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
                collection_name=self.COLLECTION_NAME,
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
            query_embedding = self.generate_embeddings(
                [query], task_type="RETRIEVAL_QUERY"
            )
            logger.debug(
                "Query embedding shape: %s (size=%s)",
                query_embedding.shape,
                query_embedding.size,
            )
            if query_embedding.size == 0:
                return []

            response = self.qdrant_client.query_points(
                collection_name=self.COLLECTION_NAME,
                query=query_embedding[0].tolist(),
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=username),
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

            logger.info("Qdrant search returned %s results", len(results))
            if results:
                logger.info(
                    "Top result score=%.6f from file=%s",
                    results[0]["score"],
                    results[0]["chunk"]["metadata"].get("filename", "unknown"),
                )

            return results

        except Exception as exc:
            logger.error("Failed to search Qdrant: %s", exc)
            return []

    def process_file_for_rag(
        self,
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
            text = self.extract_text_from_file(file_content, filename)
            if not text.strip():
                logger.info(f"No text extracted from {filename}")
                return RAGProcessResult(False, error="No extractable text found")

            metadata = {
                "user_id": username,
                "document_id": document_id,
                "filename": filename,
                "cid": cid,
                "path": path,
                "file_type": filename.lower().split('.')[-1],
            }

            chunks = self.chunk_text(text, metadata)
            if not chunks:
                logger.info(f"No chunks created from {filename}")
                return RAGProcessResult(False, error="No text chunks were created")

            success = self.add_chunks_to_vector_db(username, chunks)
            if success:
                logger.info(f"Successfully processed {filename} for RAG: {len(chunks)} chunks")
                return RAGProcessResult(True, chunk_count=len(chunks))

            return RAGProcessResult(
                False,
                error="Embedding generation or Qdrant indexing failed",
            )

        except Exception as exc:
            logger.error("Failed to process file for RAG: %s", exc)
            return RAGProcessResult(False, error=str(exc))


class LLMIntegration:
    """
    Handles integration with Language Models for generating responses
    """
    
    def __init__(self, model_type: str = "gemini", api_key: str = None):
        """
        Initialize LLM integration
        
        Args:
            model_type: Type of model ("gemini" or "local")
            api_key: API key for external services
        """
        self.model_type = model_type
        
        if model_type == "gemini" and api_key:
            self.api_key = api_key
    
    def generate_answer(self, query: str, context_chunks: List[Dict], max_tokens: int = 5000) -> str:
        """
        Generate an answer using retrieved context
        
        Args:
            query: User's question
            context_chunks: Retrieved relevant chunks
            max_tokens: Maximum tokens for response
            
        Returns:
            Generated answer
        """
        if not context_chunks:
            return "I couldn't find any relevant information in your uploaded files to answer this question."
        
        context_text = "\n\n".join([
            f"From {chunk['chunk']['metadata']['filename']}:\n{chunk['chunk']['text']}"
            for chunk in context_chunks[:3]
        ])
        
        prompt = f"""Based on the following context from the user's uploaded files, please answer their question. If the context doesn't contain enough information to answer the question, please say so.

Context:
{context_text}

Question: {query}

Answer:"""
        
        try:
            if self.model_type == "gemini":
                return self._generate_gemini_response(prompt, max_tokens)
            else:
                return self._generate_simple_response(query, context_chunks)
        except Exception as e:
            logger.error(f"Failed to generate LLM response: {e}")
            return "I encountered an error while generating the response. Please try again."
    
    def _generate_gemini_response(self, prompt: str, max_tokens: int) -> str:
        """Generate response using Gemini API"""
        try:
            model_name = "gemini-2.5-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

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

            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()
            logger.info(f"Gemini API response: {result}")
            return result['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def _generate_simple_response(self, query: str, context_chunks: List[Dict]) -> str:
        """Generate a simple extractive response when no LLM is available"""
        if not context_chunks:
            return "No relevant information found."
        
        best_chunk = context_chunks[0]
        filename = best_chunk['chunk']['metadata']['filename']
        text = best_chunk['chunk']['text']
        
        return f"Based on your file '{filename}', here's the most relevant information I found:\n\n{text}..."


rag_manager = None
llm_integration = None

def get_rag_manager() -> RAGManager:
    """Get global RAG manager instance"""
    global rag_manager
    if rag_manager is None:
        rag_manager = RAGManager()
    return rag_manager

def get_llm_integration() -> LLMIntegration:
    """Get global LLM integration instance"""
    global llm_integration
    if llm_integration is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            llm_integration = LLMIntegration("gemini", api_key)
        else:
            llm_integration = LLMIntegration("simple")
    return llm_integration
