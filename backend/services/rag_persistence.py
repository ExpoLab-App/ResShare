import logging
from enum import Enum
from typing import Optional
from backend.services.rag_utils import RAGManager
from backend.services.RSDB_kv_service import set_kv


logger = logging.getLogger(__name__)


class RAGPersistenceResult(Enum):
    SUCCESS = "SUCCESS"
    METADATA_WRITE_FAILED = "METADATA_WRITE_FAILED"
    RAG_ROLLBACK_FAILED = "RAG_ROLLBACK_FAILED"


def persist_root_with_rag_rollback(
    username,
    root_json,
    rag_manager: Optional[RAGManager]=None,
    indexed_document_id: Optional[str]=None,
) -> RAGPersistenceResult:
    """Persist the final root and remove new vectors if that write fails."""
    if set_kv(username + " ROOT", root_json):
        return RAGPersistenceResult.SUCCESS

    logger.error("Failed to persist final file metadata for user %s", username)

    if indexed_document_id is None:
        return RAGPersistenceResult.METADATA_WRITE_FAILED

    if rag_manager is None:
        logger.error(
            "Cannot roll back indexed document %s without a RAG manager",
            indexed_document_id,
        )
        return RAGPersistenceResult.RAG_ROLLBACK_FAILED

    try:
        rollback_succeeded = rag_manager.delete_documents(
            username,
            [indexed_document_id],
        )
    except Exception as exc:
        logger.error(
            "Failed to roll back indexed document %s for user %s: %s",
            indexed_document_id,
            username,
            exc,
        )
        rollback_succeeded = False

    if not rollback_succeeded:
        logger.error(
            "RAG data for document %s may be orphaned after metadata write failure",
            indexed_document_id,
        )
        return RAGPersistenceResult.RAG_ROLLBACK_FAILED

    return RAGPersistenceResult.METADATA_WRITE_FAILED
