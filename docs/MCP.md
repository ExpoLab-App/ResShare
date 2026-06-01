# ResShare MCP Server

The ResShare MCP server exposes file management, sharing, and document Q&A as [Model Context Protocol](https://modelcontextprotocol.io/) tools. It talks to the existing Flask backend over HTTP and uses the same session-based authentication as the web app.

## Architecture

```text
MCP client (Cursor / Claude Desktop)
  → stdio → mcp_server (python -m mcp_server.server)
  → HTTP + Flask session cookie
  → ResShare backend (auth, files, RAG)
```

Authorization rules are enforced only by the Flask API. The MCP server does not bypass ownership or sharing checks.

## Prerequisites

1. ResShare backend running locally (default `http://127.0.0.1:5000`).
2. Python 3.10+ with project dependencies installed:

   ```bash
   pip install -r requirements.txt
   ```

3. A ResShare user account (create via the web UI or `/signup`).

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RESSHARE_API_BASE_URL` | No | `http://127.0.0.1:5000` | Flask API base URL |
| `RESSHARE_USERNAME` | Yes | — | ResShare username for this MCP instance |
| `RESSHARE_PASSWORD` | Yes | — | Password for that user |

Set these in env variables

**Security:** Use a dedicated test account for MCP. Do not commit credentials. The MCP process holds the session cookie in memory only.

## Exposed tools (v1)

| Tool | Description |
|------|-------------|
| `get_auth_status` | Whether the session is authenticated and active username |
| `list_files` | User file tree (`root` + inbound `share_list` summary from auth-status) |
| `list_shared_items` | Items shared with the user |
| `ask_documents` | RAG Q&A over uploaded documents |
| `get_chat_stats` | Per-user vector-store stats |
| `create_folder` | Create folder under an owned path |
| `upload_file` | Upload local pdf/docx/txt (max 1 MB) |
| `share_file` | Share owned path with another username |

Destructive tools (delete user, delete file) are intentionally omitted.

All tools return a JSON object: `{ "ok", "message", "data"?, "sources"? }`.

## Run manually

From the repository root:

```bash
export RESSHARE_API_BASE_URL=http://127.0.0.1:5000
export RESSHARE_USERNAME=your-user
export RESSHARE_PASSWORD=your-password
python -m mcp_server.server
```

Logs go to stderr; stdout is reserved for MCP protocol traffic.

## Cursor configuration

Add to `.cursor/mcp.json` (or global MCP settings):

```json
{
  "mcpServers": {
    "reshare": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/absolute/path/to/ResShare",
      "env": {
        "RESSHARE_API_BASE_URL": "http://127.0.0.1:5000",
        "RESSHARE_USERNAME": "your-user",
        "RESSHARE_PASSWORD": "your-password"
      }
    }
  }
}
```

Use the same Python interpreter where `pip install -r requirements.txt` was run. Restart Cursor after changing MCP config.

## Claude Desktop configuration

Edit `claude_desktop_config.json`:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "reshare": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/absolute/path/to/ResShare",
      "env": {
        "RESSHARE_API_BASE_URL": "http://127.0.0.1:5000",
        "RESSHARE_USERNAME": "your-user",
        "RESSHARE_PASSWORD": "your-password"
      }
    }
  }
}
```

Restart Claude Desktop after saving.

## Smoke test

With the backend running and env vars set:

```bash
python scripts/mcp_smoke.py
```

This lists tools and calls `get_auth_status` over stdio.

## Unit tests

```bash
python -m unittest tests.test_mcp_server -v
```

Tests mock HTTP; they do not require a live backend.

## Limitations (v1)

- Single configured user per MCP process (personal/local workflow).
- Session cookie auth only; no API tokens or OAuth.
- stdio transport only; no hosted Streamable HTTP MCP.
- Upload reads paths from the machine where the MCP server runs; validate paths carefully.

## Future production auth

For multi-user or hosted MCP, plan to add per-user API tokens or OAuth and Bearer auth on the Flask API while keeping the same tool surface and backend authorization rules.
