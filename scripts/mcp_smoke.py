#!/usr/bin/env python3
"""
Smoke test: connect to the ResShare Streamable HTTP MCP server, list tools,
and call get_auth_status.

Requires the Flask backend and MCP HTTP server to be running with RESSHARE_*
env vars (see docs/MCP.md).

Usage (from repo root):
    python scripts/mcp_smoke.py
"""

import asyncio
import os
import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _post_json(api_base_url: str, path: str, payload: dict) -> tuple[int, dict]:
    response = requests.post(
        f"{api_base_url}{path}",
        json=payload,
        timeout=30,
    )
    try:
        data = response.json()
    except ValueError:
        data = {"message": response.text}
    return response.status_code, data


def ensure_account_ready(env: dict[str, str]) -> bool:
    api_base_url = env["RESSHARE_API_BASE_URL"].rstrip("/")
    credentials = {
        "username": env["RESSHARE_USERNAME"],
        "password": env["RESSHARE_PASSWORD"],
    }

    try:
        signup_status, signup_data = _post_json(api_base_url, "/signup", credentials)
    except requests.RequestException as exc:
        print(f"Could not reach ResShare API at {api_base_url}: {exc}", file=sys.stderr)
        return False

    signup_result = signup_data.get("result") or signup_data.get("message")
    if signup_status == 200 and signup_result == "SUCCESS":
        print(f"Created smoke-test account: {credentials['username']}")
        return True

    if signup_result != "USER_EXISTS":
        print(
            f"Signup failed for {credentials['username']}: {signup_result}",
            file=sys.stderr,
        )
        return False

    try:
        login_status, login_data = _post_json(api_base_url, "/login", credentials)
    except requests.RequestException as exc:
        print(f"Could not verify existing account login: {exc}", file=sys.stderr)
        return False

    login_result = login_data.get("result") or login_data.get("message")
    if login_status == 200 and login_result == "SUCCESS":
        print(f"Using existing smoke-test account: {credentials['username']}")
        return True

    print(
        f"Existing account login failed for {credentials['username']}: {login_result}",
        file=sys.stderr,
    )
    return False


async def main() -> int:
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    from mcp_server.config import load_mcp_env, load_server_settings

    load_mcp_env()

    for name in ("RESSHARE_USERNAME", "RESSHARE_PASSWORD"):
        if not os.environ.get(name, "").strip():
            print(
                f"Missing {name}. Set it in env variables (see docs/MCP.md).",
                file=sys.stderr,
            )
            return 1

    env = os.environ.copy()
    env.setdefault("RESSHARE_API_BASE_URL", "http://127.0.0.1:5000")
    env["RESSHARE_API_BASE_URL"] = env["RESSHARE_API_BASE_URL"].rstrip("/")

    if not ensure_account_ready(env):
        return 1

    host, port, path = load_server_settings()
    mcp_url = os.environ.get("RESSHARE_MCP_URL", "").strip()
    if not mcp_url:
        mcp_url = f"http://{host}:{port}{path}"

    print(f"Connecting to MCP server: {mcp_url}")

    async with streamable_http_client(mcp_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            tool_names = sorted(t.name for t in tools.tools)
            print("Tools:", ", ".join(tool_names))

            expected = {
                "get_auth_status",
                "list_files",
                "list_shared_items",
                "ask_documents",
                "get_chat_stats",
                "create_folder",
                "upload_file",
                "share_file",
            }
            missing = expected - set(tool_names)
            if missing:
                print("Missing tools:", ", ".join(sorted(missing)), file=sys.stderr)
                return 1

            result = await session.call_tool("get_auth_status", arguments={})
            print("get_auth_status:", result.content)

    print("Smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
