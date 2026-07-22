import unittest
from unittest.mock import Mock, patch

from backend.services.upload_service import persist_root_with_rag_rollback


class RAGPersistenceTest(unittest.TestCase):
    def test_successful_metadata_write_does_not_delete_vectors(self):
        manager = Mock()

        with patch("backend.services.upload_service.set_kv", return_value=True) as set_kv, patch(
            "backend.services.upload_service.get_vector_store"
        ) as get_vector_store:
            result = persist_root_with_rag_rollback(
                "alice",
                "root-json",
                indexed_document_id="document-id",
            )

        self.assertTrue(result)
        set_kv.assert_called_once_with("alice ROOT", "root-json")
        get_vector_store.assert_not_called()

    def test_failed_metadata_write_rolls_back_indexed_document(self):
        manager = Mock()
        manager.delete_documents.return_value = True

        with patch("backend.services.upload_service.set_kv", return_value=False), patch(
            "backend.services.upload_service.get_vector_store", return_value=manager
        ):
            result = persist_root_with_rag_rollback(
                "alice",
                "root-json",
                indexed_document_id="document-id",
            )

        self.assertFalse(result)
        manager.delete_documents.assert_called_once_with("alice", ["document-id"])

    def test_failed_metadata_write_reports_failed_rollback(self):
        manager = Mock()
        manager.delete_documents.return_value = False

        with patch("backend.services.upload_service.set_kv", return_value=False), patch(
            "backend.services.upload_service.get_vector_store", return_value=manager
        ):
            result = persist_root_with_rag_rollback(
                "alice",
                "root-json",
                indexed_document_id="document-id",
            )

        self.assertFalse(result)
        manager.delete_documents.assert_called_once_with("alice", ["document-id"])


if __name__ == "__main__":
    unittest.main()
