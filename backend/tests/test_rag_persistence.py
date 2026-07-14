import unittest
from unittest.mock import Mock, patch

from backend.rag_persistence import (
    RAGPersistenceResult,
    persist_root_with_rag_rollback,
)


class RAGPersistenceTest(unittest.TestCase):
    def test_successful_metadata_write_does_not_delete_vectors(self):
        manager = Mock()

        with patch("backend.rag_persistence.set_kv", return_value=True) as set_kv:
            result = persist_root_with_rag_rollback(
                "alice",
                "root-json",
                rag_manager=manager,
                indexed_document_id="document-id",
            )

        self.assertEqual(result, RAGPersistenceResult.SUCCESS)
        set_kv.assert_called_once_with("alice ROOT", "root-json")
        manager.delete_documents.assert_not_called()

    def test_failed_metadata_write_rolls_back_indexed_document(self):
        manager = Mock()
        manager.delete_documents.return_value = True

        with patch("backend.rag_persistence.set_kv", return_value=False):
            result = persist_root_with_rag_rollback(
                "alice",
                "root-json",
                rag_manager=manager,
                indexed_document_id="document-id",
            )

        self.assertEqual(result, RAGPersistenceResult.METADATA_WRITE_FAILED)
        manager.delete_documents.assert_called_once_with("alice", ["document-id"])

    def test_failed_metadata_write_reports_failed_rollback(self):
        manager = Mock()
        manager.delete_documents.return_value = False

        with patch("backend.rag_persistence.set_kv", return_value=False):
            result = persist_root_with_rag_rollback(
                "alice",
                "root-json",
                rag_manager=manager,
                indexed_document_id="document-id",
            )

        self.assertEqual(result, RAGPersistenceResult.RAG_ROLLBACK_FAILED)


if __name__ == "__main__":
    unittest.main()
