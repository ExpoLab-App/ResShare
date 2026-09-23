import unittest
from unittest.mock import Mock, call, patch

from backend.models.file import File
from backend.models.node import Node
from backend.services.delete_service import delete_user_data


class DeleteServiceRAGTest(unittest.TestCase):
    @staticmethod
    def root_with_indexed_file():
        root = Node("root", True)
        file_obj = File(
            "cid",
            10,
            "indexed.txt",
            document_id="420ed1bc-e802-4f56-ab88-0f71638c566d",
        )
        file_obj.mark_rag_ready(1, "gemini-embedding-001")
        root.add_child(Node("indexed.txt", False, file_obj=file_obj))
        return root

    def test_delete_user_data_removes_qdrant_data_before_kv_records(self):
        root = self.root_with_indexed_file()
        vector_store = Mock()
        vector_store.delete_user_data.return_value = True

        with patch(
            "backend.services.delete_service.get_kv", return_value=root.to_json()
        ), patch(
            "backend.services.delete_service.set_kv", return_value=True
        ) as set_kv, patch(
            "backend.services.delete_service.get_vector_store",
            return_value=vector_store,
        ):
            result = delete_user_data("alice")

        self.assertTrue(result)
        vector_store.delete_user_data.assert_called_once_with("alice")
        self.assertEqual(
            set_kv.call_args_list,
            [
                call("alice", "\n"),
                call("alice ROOT", "\n"),
                call("alice SHARE_MANAGER", "\n"),
            ],
        )

    def test_delete_user_data_keeps_kv_records_when_qdrant_cleanup_fails(self):
        root = self.root_with_indexed_file()
        vector_store = Mock()
        vector_store.delete_user_data.return_value = False

        with patch(
            "backend.services.delete_service.get_kv", return_value=root.to_json()
        ), patch(
            "backend.services.delete_service.set_kv", return_value=True
        ) as set_kv, patch(
            "backend.services.delete_service.get_vector_store",
            return_value=vector_store,
        ):
            result = delete_user_data("alice")

        self.assertFalse(result)
        vector_store.delete_user_data.assert_called_once_with("alice")
        set_kv.assert_not_called()

    def test_delete_user_data_skips_qdrant_cleanup_without_indexed_files(self):
        root = Node("root", True)
        vector_store = Mock()

        with patch(
            "backend.services.delete_service.get_kv", return_value=root.to_json()
        ), patch(
            "backend.services.delete_service.set_kv", return_value=True
        ) as set_kv, patch(
            "backend.services.delete_service.get_vector_store",
            return_value=vector_store,
        ):
            result = delete_user_data("alice")

        self.assertTrue(result)
        vector_store.delete_user_data.assert_not_called()
        self.assertEqual(set_kv.call_count, 3)


if __name__ == "__main__":
    unittest.main()
