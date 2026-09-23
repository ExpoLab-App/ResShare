from uuid import NAMESPACE_URL, uuid5
from langchain.docstore.document import Document as LangchainDocument
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import Dict, List

def chunk_text(text: str, metadata: Dict) -> List[Dict]:
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
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = text_splitter.split_documents([doc])
        
        chunk_dicts = []
        for i, chunk in enumerate(chunks):
            chunk_dict = {
                'text': chunk.page_content,
                'metadata': {
                    **chunk.metadata,
                    'chunk_index': i,
                    'chunk_id': str(uuid5( # UUIDv5 gives stable, idempotent IDs:same document + same chunk index → same UUID
                        NAMESPACE_URL,
                        (
                            f"reshare:{metadata['document_id']}:{i}"
                        ),
                    ))
                }
            }
            chunk_dicts.append(chunk_dict)
        
        return chunk_dicts