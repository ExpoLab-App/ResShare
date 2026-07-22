import unittest
from io import BytesIO
from unittest.mock import Mock, patch

from flask import Flask

from backend.controller.file_controller import register_file_routes
from backend.models.node import Node
from backend.rag.types import RAGProcessResult


class FileControllerRAGFailureTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = "test-secret"
        register_file_routes(self.app, self.app.logger)

    def test_upload_succeeds_and_records_failed_rag_status(self):
        root = Node("root", True)
        rag_result = RAGProcessResult(
            False,
            error="Qdrant unavailable",
        )
        saved_roots = []

        def capture_root(key, value):
            saved_roots.append(value)
            return True

        with patch(
            "backend.services.upload_service.get_kv", return_value=root.to_json()
        ), patch(
            "backend.services.upload_service.set_kv", side_effect=capture_root
        ), patch(
            "backend.services.upload_service.add_file_to_cluster",
            return_value="test-cid",
        ), patch(
            "backend.services.upload_service.process_file_for_rag",
            return_value=rag_result,
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
        self.assertEqual(len(saved_roots), 1)
        self.assertFalse(response.get_json()["rag_processed"])
        self.assertEqual(response.get_json()["rag_status"], "failed")
        saved_root = Node.from_json(saved_roots[-1])
        saved_file = saved_root.children["notes.txt"].file_obj
        self.assertEqual(saved_file.rag_status, "failed")
        self.assertEqual(saved_file.rag_error, "Qdrant unavailable")

    def test_upload_records_failed_rag_status_when_processing_raises(self):
        root = Node("root", True)
        saved_roots = []

        with patch(
            "backend.services.upload_service.get_kv", return_value=root.to_json()
        ), patch(
            "backend.services.upload_service.set_kv",
            side_effect=lambda key, value: saved_roots.append(value) or True,
        ), patch(
            "backend.services.upload_service.add_file_to_cluster",
            return_value="test-cid",
        ), patch(
            "backend.services.upload_service.process_file_for_rag",
            side_effect=RuntimeError("Qdrant unavailable"),
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
        self.assertEqual(len(saved_roots), 1)
        self.assertFalse(response.get_json()["rag_processed"])
        self.assertEqual(response.get_json()["rag_status"], "failed")
        saved_root = Node.from_json(saved_roots[-1])
        saved_file = saved_root.children["notes.txt"].file_obj
        self.assertEqual(saved_file.rag_status, "failed")
        self.assertEqual(saved_file.rag_error, "Qdrant unavailable")

    def test_upload_rolls_back_rag_when_final_metadata_write_fails(self):
        root = Node("root", True)
        manager = Mock()
        manager.embedding_model_name = "gemini-embedding-001"
        rag_result = RAGProcessResult(
            True,
            chunk_count=1,
        )
        manager.delete_documents.return_value = True

        with patch(
            "backend.services.upload_service.get_kv", return_value=root.to_json()
        ), patch(
            "backend.services.upload_service.set_kv", return_value=False
        ), patch(
            "backend.services.upload_service.add_file_to_cluster",
            return_value="test-cid",
        ), patch(
            "backend.services.upload_service.process_file_for_rag",
            return_value=rag_result,
        ) as process_file_for_rag, patch(
            "backend.services.upload_service.get_vector_store", return_value=manager
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

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["message"], "KV_SERVICE_ERROR")
        manager.delete_documents.assert_called_once()
        self.assertEqual(
            manager.delete_documents.call_args.args,
            ("alice", [process_file_for_rag.call_args.args[4]]),
        )

    def test_upload_reports_failed_rollback_after_metadata_write_fails(self):
        root = Node("root", True)
        manager = Mock()
        manager.embedding_model_name = "gemini-embedding-001"
        rag_result = RAGProcessResult(
            True,
            chunk_count=1,
        )
        manager.delete_documents.return_value = False

        with patch(
            "backend.services.upload_service.get_kv", return_value=root.to_json()
        ), patch(
            "backend.services.upload_service.set_kv", return_value=False
        ), patch(
            "backend.services.upload_service.add_file_to_cluster",
            return_value="test-cid",
        ), patch(
            "backend.services.upload_service.process_file_for_rag",
            return_value=rag_result,
        ), patch(
            "backend.services.upload_service.get_vector_store", return_value=manager
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

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["message"], "KV_SERVICE_ERROR")
        manager.delete_documents.assert_called_once()

    def test_upload_persists_skipped_file_once(self):
        root = Node("root", True)
        saved_roots = []

        with patch(
            "backend.services.upload_service.get_kv", return_value=root.to_json()
        ), patch(
            "backend.services.upload_service.set_kv",
            side_effect=lambda key, value: saved_roots.append(value) or True,
        ), patch(
            "backend.services.upload_service.add_file_to_cluster",
            return_value="test-cid",
        ), patch(
            "backend.services.upload_service.process_file_for_rag"
        ) as process_file_for_rag:
            with self.app.test_client() as client:
                with client.session_transaction() as client_session:
                    client_session["username"] = "alice"
                response = client.post(
                    "/upload",
                    data={
                        "path": "",
                        "skip_ai_processing": "true",
                        "file": (BytesIO(b"hello world"), "notes.txt"),
                    },
                    content_type="multipart/form-data",
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(saved_roots), 1)
        saved_root = Node.from_json(saved_roots[0])
        self.assertEqual(saved_root.children["notes.txt"].file_obj.rag_status, "skipped")
        process_file_for_rag.assert_not_called()


if __name__ == "__main__":
    unittest.main()
