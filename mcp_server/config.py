import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class McpSettings:
    api_base_url: str
    username: str
    password: str


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


def load_settings() -> McpSettings:
    load_mcp_env()
    base = os.environ.get("RESSHARE_API_BASE_URL", "http://127.0.0.1:5000").strip()
    return McpSettings(
        api_base_url=base.rstrip("/"),
        username=_require("RESSHARE_USERNAME"),
        password=_require("RESSHARE_PASSWORD"),
    )
