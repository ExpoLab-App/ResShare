import unittest
from io import BytesIO
from unittest.mock import Mock, patch

from flask import Flask

from backend.controller.file_controller import register_file_routes
from backend.node import Node
from backend.rag_utils import RAGProcessResult


class FileControllerRAGFailureTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = "test-secret"
        register_file_routes(self.app, self.app.logger)

    def test_upload_succeeds_and_records_failed_rag_status(self):
        root = Node("root", True)
        manager = Mock()
        manager.embedding_model_name = "gemini-embedding-001"
        manager.process_file_for_rag.return_value = RAGProcessResult(
            False,
            error="Qdrant unavailable",
        )
        saved_roots = []

        def capture_root(key, value):
            saved_roots.append(value)
            return True

        with patch(
            "backend.controller.file_controller.get_kv", return_value=root.to_json()
        ), patch(
            "backend.controller.file_controller.set_kv", side_effect=capture_root
        ), patch(
            "backend.controller.file_controller.add_file_to_cluster",
            return_value="test-cid",
        ), patch(
            "backend.controller.file_controller.get_rag_manager", return_value=manager
        ):
            with self.app.test_client() as client:
                with client.session_transaction() as client_session:
                    client_session["username"] = "alice"
                response = client.post(
                    "/upload",
                    data={
                        "path": "",
                        "file": (BytesIO(b"hello world"), "notes.txt"),
                    },
                    content_type="multipart/form-data",
                )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()["rag_processed"])
        self.assertEqual(response.get_json()["rag_status"], "failed")
        saved_root = Node.from_json(saved_roots[-1])
        saved_file = saved_root.children["notes.txt"].file_obj
        self.assertEqual(saved_file.rag_status, "failed")
        self.assertEqual(saved_file.rag_error, "Qdrant unavailable")

    def test_upload_records_failed_rag_status_when_processing_raises(self):
        root = Node("root", True)
        manager = Mock()
        manager.embedding_model_name = "gemini-embedding-001"
        manager.process_file_for_rag.side_effect = RuntimeError("Qdrant unavailable")
        saved_roots = []

        with patch(
            "backend.controller.file_controller.get_kv", return_value=root.to_json()
        ), patch(
            "backend.controller.file_controller.set_kv",
            side_effect=lambda key, value: saved_roots.append(value) or True,
        ), patch(
            "backend.controller.file_controller.add_file_to_cluster",
            return_value="test-cid",
        ), patch(
            "backend.controller.file_controller.get_rag_manager", return_value=manager
        ):
            with self.app.test_client() as client:
                with client.session_transaction() as client_session:
                    client_session["username"] = "alice"
                response = client.post(
                    "/upload",
                    data={
                        "path": "",
                        "file": (BytesIO(b"hello world"), "notes.txt"),
                    },
                    content_type="multipart/form-data",
                )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()["rag_processed"])
        self.assertEqual(response.get_json()["rag_status"], "failed")
        saved_root = Node.from_json(saved_roots[-1])
        saved_file = saved_root.children["notes.txt"].file_obj
        self.assertEqual(saved_file.rag_status, "failed")
        self.assertEqual(saved_file.rag_error, "Qdrant unavailable")


if __name__ == "__main__":
    unittest.main()
