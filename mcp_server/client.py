import logging
from pathlib import Path
from typing import Any, Optional

import requests

from mcp_server.config import McpSettings

logger = logging.getLogger(__name__)


class ResShareApiError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        payload: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload or {}


class ResShareClient:
    """HTTP client for the ResShare Flask API using session-cookie auth."""

    def __init__(self, settings: McpSettings) -> None:
        self._settings = settings
        self._session = requests.Session()
        self._authenticated = False

    @property
    def base_url(self) -> str:
        return self._settings.api_base_url

    def login(self) -> dict[str, Any]:
        response = self._session.post(
            f"{self.base_url}/login",
            json={
                "username": self._settings.username,
                "password": self._settings.password,
            },
            timeout=60,
        )
        payload = _parse_json(response)
        if response.status_code != 200:
            self._authenticated = False
            raise ResShareApiError(
                payload.get("message") or payload.get("result") or "Login failed",
                status_code=response.status_code,
                payload=payload,
            )
        self._authenticated = True
        return payload

    def request(
        self,
        method: str,
        path: str,
        *,
        retry_auth: bool = True,
        **kwargs: Any,
    ) -> requests.Response:
        if not self._authenticated:
            self.login()

        timeout = kwargs.pop("timeout", 120)
        url = f"{self.base_url}{path}"
        response = self._session.request(method, url, timeout=timeout, **kwargs)

        if response.status_code == 401 and retry_auth:
            logger.info("Session expired; re-authenticating")
            self.login()
            response = self._session.request(method, url, timeout=timeout, **kwargs)

        return response

    def get_auth_status(self) -> dict[str, Any]:
        response = self._session.get(f"{self.base_url}/auth-status", timeout=30)
        payload = _parse_json(response)
        if response.status_code == 200 and payload.get("authenticated"):
            self._authenticated = True
            return payload
        self._authenticated = False
        if response.status_code == 401:
            return {"authenticated": False}
        raise ResShareApiError(
            payload.get("message") or "Failed to check auth status",
            status_code=response.status_code,
            payload=payload,
        )

    def list_files(self) -> dict[str, Any]:
        return self._json_request("GET", "/auth-status")

    def list_shared_items(self) -> dict[str, Any]:
        return self._json_request("GET", "/shared")

    def download_file(self, path: str, *, is_shared: bool = False) -> tuple[bytes, str]:
        response = self.request(
            "POST",
            "/download",
            json={"path": path, "is_shared": is_shared},
            timeout=120,
        )
        if response.ok:
            filename = _filename_from_response(response, path)
            return response.content, filename

        payload: dict[str, Any] = {}
        try:
            parsed = response.json()
            if isinstance(parsed, dict):
                payload = parsed
        except ValueError:
            pass

        message = (
            payload.get("message")
            or payload.get("result")
            or f"Download failed with status {response.status_code}"
        )
        raise ResShareApiError(
            message,
            status_code=response.status_code,
            payload=payload,
        )

    def get_chat_stats(self) -> dict[str, Any]:
        return self._json_request("GET", "/chat/stats")

    def create_folder(self, folder_path: str) -> dict[str, Any]:
        return self._json_request(
            "POST",
            "/create-folder",
            json={"folder_path": folder_path},
        )

    def share_file(self, path: str, target: str) -> dict[str, Any]:
        return self._json_request(
            "POST",
            "/share",
            json={"path": path, "target": target},
        )

    def upload_file(
        self,
        local_path: Path,
        path: str,
        *,
        skip_ai_processing: bool = False,
    ) -> dict[str, Any]:
        response = self._upload_file_once(local_path, path, skip_ai_processing)
        if response.status_code == 401:
            logger.info("Session expired during upload; re-authenticating")
            self.login()
            response = self._upload_file_once(local_path, path, skip_ai_processing)
        return _parse_json(response, expect_ok=True)

    def _upload_file_once(
        self,
        local_path: Path,
        path: str,
        skip_ai_processing: bool,
    ) -> requests.Response:
        with local_path.open("rb") as file_handle:
            return self.request(
                "POST",
                "/upload",
                retry_auth=False,
                files={"file": (local_path.name, file_handle)},
                data={
                    "path": path,
                    "skip_ai_processing": str(skip_ai_processing).lower(),
                },
            )

    def _json_request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        response = self.request(method, path, **kwargs)
        return _parse_json(response, expect_ok=True)


def _filename_from_response(response: requests.Response, path: str) -> str:
    content_disposition = response.headers.get("Content-Disposition", "")
    marker = "filename="
    if marker in content_disposition:
        raw_name = content_disposition.split(marker, maxsplit=1)[1].strip().strip('"')
        if raw_name:
            return raw_name
    return path.rsplit("/", maxsplit=1)[-1]


def _parse_json(
    response: requests.Response,
    *,
    expect_ok: bool = False,
) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise ResShareApiError(
            "Invalid JSON response from ResShare API",
            status_code=response.status_code,
        ) from exc

    if not isinstance(payload, dict):
        raise ResShareApiError(
            "Unexpected response shape from ResShare API",
            status_code=response.status_code,
            payload={"raw": payload},
        )

    if expect_ok and not response.ok:
        message = (
            payload.get("message")
            or payload.get("result")
            or payload.get("error")
            or f"Request failed with status {response.status_code}"
        )
        raise ResShareApiError(message, status_code=response.status_code, payload=payload)

    return payload
