import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[1]

MCP_PATH = "/mcp"


@dataclass(frozen=True)
class McpSettings:
    api_base_url: str
    username: str
    password: str
    host: str
    port: int
    path: str


def load_mcp_env() -> None:
    """Load MCP env vars from repo-root .env"""
    env_file = _REPO_ROOT / ".env"
    if env_file.is_file():
        load_dotenv(env_file)


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _optional_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name, "").strip()
    if not raw_value:
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def load_server_settings() -> tuple[str, int, str]:
    load_mcp_env()
    return _read_server_settings()


def _read_server_settings() -> tuple[str, int, str]:
    host = os.environ.get("RESSHARE_MCP_HOST", "127.0.0.1").strip() or "127.0.0.1"
    port = _optional_int("RESSHARE_MCP_PORT", 8126)
    return host, port, MCP_PATH


def load_settings() -> McpSettings:
    load_mcp_env()
    base = os.environ.get("RESSHARE_API_BASE_URL", "http://127.0.0.1:5000").strip()
    host, port, path = _read_server_settings()
    return McpSettings(
        api_base_url=base.rstrip("/"),
        username=_require("RESSHARE_USERNAME"),
        password=_require("RESSHARE_PASSWORD"),
        host=host,
        port=port,
        path=path,
    )
