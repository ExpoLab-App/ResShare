import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from mcp_server.client import ResShareApiError, ResShareClient
from mcp_server.config import McpSettings
from mcp_server.validation import (
    ValidationError,
    validate_file_path,
    validate_folder_path,
    validate_local_upload_file,
    validate_share_path,
)


class TestValidation(unittest.TestCase):
    def test_rejects_path_traversal(self) -> None:
        with self.assertRaises(ValidationError):
            validate_folder_path("root/../secret")

    def test_rejects_empty_file_path(self) -> None:
        with self.assertRaises(ValidationError):
            validate_file_path("   ")

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
    def test_download_file_retries_auth_on_401(self, session_cls: MagicMock) -> None:
        session = session_cls.return_value
        client = ResShareClient(self.settings)
        client._authenticated = True

        unauthorized = MagicMock()
        unauthorized.status_code = 401
        unauthorized.ok = False
        unauthorized.headers = {}
        unauthorized.content = b""
        unauthorized.json.return_value = {"message": "NOT_LOGGED_IN"}

        login_ok = _mock_response(200, {"result": "SUCCESS"})
        download_ok = MagicMock()
        download_ok.status_code = 200
        download_ok.ok = True
        download_ok.headers = {"Content-Disposition": 'attachment; filename="note.txt"'}
        download_ok.content = b"hello world"

        session.request.side_effect = [unauthorized, download_ok]
        session.post.return_value = login_ok

        file_bytes, filename = client.download_file("root/doc/note.txt")

        self.assertEqual(file_bytes, b"hello world")
        self.assertEqual(filename, "note.txt")
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
    def test_read_file_validation(self, get_client: MagicMock) -> None:
        from mcp_server import server

        result = server.read_file("  ")

        self.assertFalse(result["ok"])
        get_client.assert_not_called()

    @patch("mcp_server.server._get_client")
    def test_read_file_returns_content(self, get_client: MagicMock) -> None:
        from mcp_server import server

        client = MagicMock()
        client.download_file.return_value = (b"line one\nline two", "brief.txt")
        get_client.return_value = client

        result = server.read_file("root/doc/brief.txt")

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["filename"], "brief.txt")
        self.assertEqual(result["data"]["content"], "line one\nline two")
        client.download_file.assert_called_once_with("root/doc/brief.txt", is_shared=False)

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


class TestSportsMemorySeed(unittest.TestCase):
    def test_seed_corpus_has_separate_domain_files(self) -> None:
        from scripts.seed_2026_sports_memory import SPORTS_BRIEFINGS

        expected_files = {
            "2026_sports_world_cup_brief.txt",
            "2026_sports_winter_olympics_brief.txt",
            "2026_sports_formula_1_brief.txt",
            "2026_sports_ufc_recent_events_brief.txt",
            "2026_sports_ipl_playoffs_brief.txt",
            "2026_sports_premier_league_brief.txt",
            "2026_sports_bundesliga_brief.txt",
            "2026_sports_laliga_brief.txt",
        }

        self.assertEqual(set(SPORTS_BRIEFINGS), expected_files)

    def test_seed_corpus_forces_file_selection(self) -> None:
        from scripts.seed_2026_sports_memory import SPORTS_BRIEFINGS

        self.assertIn("UFC Fight Night: Muhammad vs Bonfim", SPORTS_BRIEFINGS["2026_sports_ufc_recent_events_brief.txt"])
        self.assertIn("Qualifier 1: Royal Challengers Bengaluru vs Gujarat Titans", SPORTS_BRIEFINGS["2026_sports_ipl_playoffs_brief.txt"])
        self.assertIn("Arsenal won the 2025/26 Premier League title", SPORTS_BRIEFINGS["2026_sports_premier_league_brief.txt"])
        self.assertIn("Bayern Munich finished first", SPORTS_BRIEFINGS["2026_sports_bundesliga_brief.txt"])
        self.assertIn("Matchday 36 snapshot", SPORTS_BRIEFINGS["2026_sports_laliga_brief.txt"])


if __name__ == "__main__":
    unittest.main()
