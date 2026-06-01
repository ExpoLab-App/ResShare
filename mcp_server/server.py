"""
ResShare MCP server (stdio).

Run from repository root:
    python -m mcp_server.server
"""

import logging
import sys
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from mcp_server.client import ResShareApiError, ResShareClient
from mcp_server.config import load_settings
from mcp_server.responses import tool_response
from mcp_server.validation import (
    ValidationError,
    validate_chat_query,
    validate_folder_path,
    validate_local_upload_file,
    validate_share_path,
    validate_target_username,
)

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("reshare", json_response=True)

_client: Optional[ResShareClient] = None


def _get_client() -> ResShareClient:
    global _client
    if _client is None:
        settings = load_settings()
        _client = ResShareClient(settings)
        _client.login()
    return _client


def _validation_failure(exc: ValidationError) -> dict[str, Any]:
    return tool_response(ok=False, message=str(exc))


def _api_failure(exc: ResShareApiError) -> dict[str, Any]:
    if exc.status_code == 401:
        return tool_response(ok=False, message="Not authenticated or session expired")
    return tool_response(ok=False, message=str(exc), data=exc.payload or None)


@mcp.tool()
def get_auth_status() -> dict[str, Any]:
    """Return whether the configured ResShare session is authenticated and the active username."""
    try:
        api_client = _get_client()
        payload = api_client.get_auth_status()
        if not payload.get("authenticated"):
            return tool_response(ok=False, message="Not authenticated")
        return tool_response(
            ok=True,
            message="Authenticated",
            data={
                "authenticated": True,
                "username": payload.get("username"),
            },
        )
    except (ValidationError, ValueError) as exc:
        return _validation_failure(exc)
    except ResShareApiError as exc:
        return _api_failure(exc)


@mcp.tool()
def list_files() -> dict[str, Any]:
    """List the authenticated user's file tree (same data as /auth-status root)."""
    try:
        api_client = _get_client()
        payload = api_client.list_files()
        if not payload.get("authenticated"):
            return tool_response(ok=False, message="Not authenticated")
        return tool_response(
            ok=True,
            message="OK",
            data={
                "username": payload.get("username"),
                "root": payload.get("root"),
                "share_list": payload.get("share_list"),
            },
        )
    except ValidationError as exc:
        return _validation_failure(exc)
    except ResShareApiError as exc:
        return _api_failure(exc)


@mcp.tool()
def list_shared_items() -> dict[str, Any]:
    """List files and folders shared with the authenticated user."""
    try:
        api_client = _get_client()
        payload = api_client.list_shared_items()
        return tool_response(
            ok=True,
            message="OK",
            data={"share_list": payload.get("share_list", [])},
        )
    except ValidationError as exc:
        return _validation_failure(exc)
    except ResShareApiError as exc:
        return _api_failure(exc)


@mcp.tool()
def ask_documents(query: str) -> dict[str, Any]:
    """Ask a question over the user's uploaded documents using the RAG chat flow."""
    try:
        cleaned = validate_chat_query(query)
        api_client = _get_client()
        payload = api_client.ask_documents(cleaned)
        sources = payload.get("sources", [])
        return tool_response(
            ok=True,
            message="OK",
            data={
                "answer": payload.get("answer", ""),
                "chunks_found": payload.get("chunks_found", 0),
            },
            sources=sources,
        )
    except ValidationError as exc:
        return _validation_failure(exc)
    except ResShareApiError as exc:
        return _api_failure(exc)


@mcp.tool()
def get_chat_stats() -> dict[str, Any]:
    """Return per-user RAG / vector-store statistics."""
    try:
        api_client = _get_client()
        payload = api_client.get_chat_stats()
        return tool_response(ok=True, message="OK", data=payload)
    except ValidationError as exc:
        return _validation_failure(exc)
    except ResShareApiError as exc:
        return _api_failure(exc)


@mcp.tool()
def create_folder(folder_path: str) -> dict[str, Any]:
    """Create a folder at a user-owned path (e.g. root/doc/reports)."""
    try:
        normalized = validate_folder_path(folder_path)
        api_client = _get_client()
        payload = api_client.create_folder(normalized)
        return tool_response(
            ok=True,
            message=payload.get("result", "SUCCESS"),
            data={"root": payload.get("root")},
        )
    except ValidationError as exc:
        return _validation_failure(exc)
    except ResShareApiError as exc:
        return _api_failure(exc)


@mcp.tool()
def upload_file(
    local_path: str,
    path: str,
    skip_ai_processing: bool = False,
) -> dict[str, Any]:
    """Upload a local file (pdf, docx, txt; max 1 MB) to a user-owned parent path."""
    try:
        file_path, _ = validate_local_upload_file(local_path)
        parent_path = path.strip().strip("/")
        api_client = _get_client()
        payload = api_client.upload_file(
            file_path,
            parent_path,
            skip_ai_processing=skip_ai_processing,
        )
        return tool_response(
            ok=True,
            message=payload.get("message", "SUCCESS"),
            data={
                "root": payload.get("root"),
                "rag_processed": payload.get("rag_processed"),
                "rag_skipped": payload.get("rag_skipped"),
                "skip_ai_processing": payload.get("skip_ai_processing"),
            },
        )
    except ValidationError as exc:
        return _validation_failure(exc)
    except ResShareApiError as exc:
        return _api_failure(exc)


@mcp.tool()
def share_file(path: str, target: str) -> dict[str, Any]:
    """Share a user-owned file or folder path with another ResShare username."""
    try:
        normalized_path = validate_share_path(path)
        target_user = validate_target_username(target)
        api_client = _get_client()
        payload = api_client.share_file(normalized_path, target_user)
        return tool_response(
            ok=True,
            message=payload.get("message", "SUCCESS"),
        )
    except ValidationError as exc:
        return _validation_failure(exc)
    except ResShareApiError as exc:
        return _api_failure(exc)


def main() -> None:
    try:
        load_settings()
    except ValueError as exc:
        logger.error("%s", exc)
        sys.exit(1)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
