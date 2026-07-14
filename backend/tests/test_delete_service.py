import unittest
from unittest.mock import Mock, patch

from flask import Flask, session

from backend.delete_service import delete_node
from backend.file import File
from backend.node import Node


class DeleteServiceRAGTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = "test-secret"

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
        return root, file_obj

    def test_delete_removes_qdrant_chunks_before_file_record(self):
        root, file_obj = self.root_with_indexed_file()
        manager = Mock()
        manager.delete_documents.return_value = True

        with self.app.test_request_context("/"):
            session["username"] = "alice"
            with patch("backend.delete_service.get_kv", return_value=root.to_json()), patch(
                "backend.delete_service.set_kv", return_value=True
            ) as set_kv, patch(
                "backend.delete_service.get_rag_manager", return_value=manager
            ):
                response, status = delete_node(
                    {"node_path": "indexed.txt", "delete_in_root": True}
                )

        self.assertEqual(status, 200)
        manager.delete_documents.assert_called_once_with("alice", [file_obj.document_id])
        saved_root = Node.from_json(set_kv.call_args.args[1])
        self.assertNotIn("indexed.txt", saved_root.children)

    def test_delete_keeps_file_when_qdrant_cleanup_fails(self):
        root, _ = self.root_with_indexed_file()
        manager = Mock()
        manager.delete_documents.return_value = False

        with self.app.test_request_context("/"):
            session["username"] = "alice"
            with patch("backend.delete_service.get_kv", return_value=root.to_json()), patch(
                "backend.delete_service.set_kv", return_value=True
            ) as set_kv, patch(
                "backend.delete_service.get_rag_manager", return_value=manager
            ):
                response, status = delete_node(
                    {"node_path": "indexed.txt", "delete_in_root": True}
                )

        self.assertEqual(status, 503)
        self.assertEqual(response.get_json()["message"], "RAG_DELETE_FAILED")
        set_kv.assert_not_called()

    def test_folder_delete_removes_all_indexed_descendants(self):
        root = Node("root", True)
        folder = Node("docs", True)
        first = File(
            "first-cid",
            10,
            "first.txt",
            document_id="95357bf7-0a52-45f2-b048-1032e951bed1",
        )
        second = File(
            "second-cid",
            10,
            "second.txt",
            document_id="b4749b34-8c68-4412-86bb-e0a20a0eaa70",
        )
        first.mark_rag_ready(1, "gemini-embedding-001")
        second.mark_rag_ready(1, "gemini-embedding-001")
        folder.add_child(Node("first.txt", False, file_obj=first))
        folder.add_child(Node("second.txt", False, file_obj=second))
        root.add_child(folder)
        manager = Mock()
        manager.delete_documents.return_value = True

        with self.app.test_request_context("/"):
            session["username"] = "alice"
            with patch("backend.delete_service.get_kv", return_value=root.to_json()), patch(
                "backend.delete_service.set_kv", return_value=True
            ) as set_kv, patch(
                "backend.delete_service.get_rag_manager", return_value=manager
            ):
                _, status = delete_node(
                    {"node_path": "docs", "delete_in_root": True}
                )

        self.assertEqual(status, 200)
        manager.delete_documents.assert_called_once_with(
            "alice", [first.document_id, second.document_id]
        )
        saved_root = Node.from_json(set_kv.call_args.args[1])
        self.assertNotIn("docs", saved_root.children)


if __name__ == "__main__":
    unittest.main()
