import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from mcp_server.client import ResShareApiError, ResShareClient
from mcp_server.config import McpSettings
from mcp_server.validation import (
    ValidationError,
    validate_chat_query,
    validate_folder_path,
    validate_local_upload_file,
    validate_share_path,
)


class TestValidation(unittest.TestCase):
    def test_rejects_path_traversal(self) -> None:
        with self.assertRaises(ValidationError):
            validate_folder_path("root/../secret")

    def test_rejects_empty_query(self) -> None:
        with self.assertRaises(ValidationError):
            validate_chat_query("   ")

    def test_rejects_sharing_root(self) -> None:
        with self.assertRaises(ValidationError):
            validate_share_path("root")

    def test_validates_local_file_missing(self) -> None:
        with self.assertRaises(ValidationError):
            validate_local_upload_file("/nonexistent/file.txt")


def _mock_response(
    status_code: int,
    payload: dict,
    *,
    ok: bool | None = None,
) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.ok = ok if ok is not None else 200 <= status_code < 300
    response.json.return_value = payload
    return response


class TestResShareClient(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = McpSettings(
            api_base_url="http://127.0.0.1:5000",
            username="alice",
            password="Pass@123",
            host="127.0.0.1",
            port=8126,
            path="/mcp",
        )

    @patch("mcp_server.client.requests.Session")
    def test_login_success(self, session_cls: MagicMock) -> None:
        session = session_cls.return_value
        session.post.return_value = _mock_response(
            200, {"result": "SUCCESS", "root": {}}
        )
        client = ResShareClient(self.settings)

        payload = client.login()

        self.assertTrue(client._authenticated)
        self.assertEqual(payload["result"], "SUCCESS")
        session.post.assert_called_once()

    @patch("mcp_server.client.requests.Session")
    def test_login_failure(self, session_cls: MagicMock) -> None:
        session = session_cls.return_value
        session.post.return_value = _mock_response(
            401, {"message": "INCORRECT_PASSWORD"}, ok=False
        )
        client = ResShareClient(self.settings)

        with self.assertRaises(ResShareApiError):
            client.login()

        self.assertFalse(client._authenticated)

    @patch("mcp_server.client.requests.Session")
    def test_ask_documents_retries_auth_on_401(self, session_cls: MagicMock) -> None:
        session = session_cls.return_value
        client = ResShareClient(self.settings)
        client._authenticated = True

        unauthorized = _mock_response(401, {"message": "NOT_LOGGED_IN"}, ok=False)
        login_ok = _mock_response(200, {"result": "SUCCESS"})
        chat_ok = _mock_response(
            200,
            {"answer": "hello", "sources": [], "chunks_found": 1},
        )

        session.request.side_effect = [unauthorized, chat_ok]
        session.post.return_value = login_ok

        payload = client.ask_documents("what is in my docs?")

        self.assertEqual(payload["answer"], "hello")
        self.assertEqual(session.post.call_count, 1)

    @patch("mcp_server.client.requests.Session")
    def test_upload_file_reopens_stream_on_auth_retry(
        self,
        session_cls: MagicMock,
    ) -> None:
        session = session_cls.return_value
        client = ResShareClient(self.settings)
        client._authenticated = True

        file_content = b"upload body"
        uploaded_bodies = []

        unauthorized = _mock_response(401, {"message": "NOT_LOGGED_IN"}, ok=False)
        login_ok = _mock_response(200, {"result": "SUCCESS"})
        upload_ok = _mock_response(200, {"message": "SUCCESS"})

        def request_side_effect(*_args, **kwargs):
            file_handle = kwargs["files"]["file"][1]
            uploaded_bodies.append(file_handle.read())
            return unauthorized if len(uploaded_bodies) == 1 else upload_ok

        session.request.side_effect = request_side_effect
        session.post.return_value = login_ok

        with TemporaryDirectory() as temp_dir:
            local_path = Path(temp_dir) / "note.txt"
            local_path.write_bytes(file_content)

            payload = client.upload_file(
                local_path,
                "root",
                skip_ai_processing=True,
            )

        self.assertEqual(payload["message"], "SUCCESS")
        self.assertEqual(uploaded_bodies, [file_content, file_content])
        self.assertEqual(session.post.call_count, 1)
        self.assertEqual(session.request.call_count, 2)


class TestMcpTools(unittest.TestCase):
    @patch("mcp_server.server._get_client")
    def test_get_auth_status_authenticated(self, get_client: MagicMock) -> None:
        from mcp_server import server

        client = MagicMock()
        client.get_auth_status.return_value = {
            "authenticated": True,
            "username": "alice",
        }
        get_client.return_value = client

        result = server.get_auth_status()

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["username"], "alice")

    @patch("mcp_server.server._get_client")
    def test_ask_documents_validation(self, get_client: MagicMock) -> None:
        from mcp_server import server

        result = server.ask_documents("  ")

        self.assertFalse(result["ok"])
        get_client.assert_not_called()

    @patch("mcp_server.server.load_settings")
    @patch("mcp_server.server.mcp.run")
    def test_main_runs_streamable_http_transport(
        self,
        run: MagicMock,
        load_settings: MagicMock,
    ) -> None:
        from mcp_server import server

        load_settings.return_value = McpSettings(
            api_base_url="http://127.0.0.1:5000",
            username="alice",
            password="Pass@123",
            host="127.0.0.1",
            port=8126,
            path="/mcp",
        )

        server.main()

        run.assert_called_once_with(transport="streamable-http")


if __name__ == "__main__":
    unittest.main()
