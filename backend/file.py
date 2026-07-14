from datetime import datetime, timezone
from typing import Optional
from uuid import NAMESPACE_URL, uuid4, uuid5


class File:
    def __init__(
        self,
        cid,
        size,
        filename,
        creation_date=None,
        document_id=None,
        mime_type=None,
        rag_status="not_indexed",
        chunk_count=0,
        embedding_model=None,
        indexed_at=None,
        rag_error=None,
    ):
        self.cid = cid  # IPFS CID
        self.size = size
        self.filename = filename
        self.creation_date = creation_date or datetime.now()
        self.document_id = document_id or str(uuid4())
        self.mime_type = mime_type
        self.rag_status = rag_status
        self.chunk_count = chunk_count
        self.embedding_model = embedding_model
        self.indexed_at = indexed_at
        self.rag_error = rag_error


    def mark_rag_ready(self, chunk_count, embedding_model):
        self.rag_status = "ready"
        self.chunk_count = chunk_count
        self.embedding_model = embedding_model
        self.indexed_at = datetime.now(timezone.utc)
        self.rag_error = None

    def mark_rag_failed(self, error, embedding_model):
        self.rag_status = "failed"
        self.chunk_count = 0
        self.embedding_model = embedding_model
        self.indexed_at = None
        self.rag_error = error

    def to_dict(self):
        return {
            "cid": self.cid,
            "size": self.size,
            "filename": self.filename,
            "creation_date": self.creation_date.isoformat(),
            "document_id": self.document_id,
            "mime_type": self.mime_type,
            "rag_status": self.rag_status,
            "chunk_count": self.chunk_count,
            "embedding_model": self.embedding_model,
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
            "rag_error": self.rag_error,
        }

    @classmethod
    def from_dict(cls, data):
        creation_date = datetime.fromisoformat(data["creation_date"])
        indexed_at_value: Optional[str] = data.get("indexed_at")
        document_id = data.get("document_id")

        return cls(
            cid=data["cid"],
            size=data["size"],
            filename=data["filename"],
            creation_date=creation_date,
            document_id=document_id,
            mime_type=data.get("mime_type"),
            rag_status=data.get("rag_status", "not_indexed"),
            chunk_count=data.get("chunk_count", 0),
            embedding_model=data.get("embedding_model"),
            indexed_at=datetime.fromisoformat(indexed_at_value) if indexed_at_value else None,
            rag_error=data.get("rag_error"),
        )

    def __repr__(self):
        return f"File({self.filename}, CID={self.cid}, Size={self.size} bytes, Created={self.creation_date})"

    def __eq__(self, other):
        if not isinstance(other, File):
            return False
        return (
            self.cid == other.cid
            and self.size == other.size
            and self.filename == other.filename
            and self.creation_date == other.creation_date
            and self.document_id == other.document_id
            and self.mime_type == other.mime_type
            and self.rag_status == other.rag_status
            and self.chunk_count == other.chunk_count
            and self.embedding_model == other.embedding_model
            and self.indexed_at == other.indexed_at
            and self.rag_error == other.rag_error
        )

    def __hash__(self):
        return hash(
            (self.cid, self.size, self.filename, self.creation_date, self.document_id)
        )
