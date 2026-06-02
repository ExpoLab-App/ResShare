# ResShare MCP Server

The ResShare MCP server exposes file management, sharing, and document Q&A as
[Model Context Protocol](https://modelcontextprotocol.io/) tools over
Streamable HTTP. 

## Architecture

```text
MCP client
  -> HTTP Streamable MCP endpoint http://127.0.0.1:8126/mcp
  -> ResShare MCP server
  -> ResShare Flask API http://127.0.0.1:5000
```

Authorization is enforced by the Flask API. The MCP server logs in with the
configured ResShare account and holds that session cookie in memory.

## Prerequisites

1. ResShare backend running locally, default `http://127.0.0.1:5000`.
2. Python dependencies installed:

   ```bash
   pip install -r requirements.txt
   ```

3. A ResShare user account. The smoke script can create or verify the account
   through `/signup` and `/login`.

## Environment Variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `RESSHARE_API_BASE_URL` | No | `http://127.0.0.1:5000` | Flask API base URL |
| `RESSHARE_USERNAME` | Yes | - | ResShare username used by this MCP server |
| `RESSHARE_PASSWORD` | Yes | - | Password for the configured user |
| `RESSHARE_MCP_HOST` | No | `127.0.0.1` | MCP HTTP bind host |
| `RESSHARE_MCP_PORT` | No | `8126` | MCP HTTP bind port |
| `RESSHARE_MCP_PATH` | No | `/mcp` | Streamable HTTP MCP path |
| `RESSHARE_MCP_URL` | No | derived from host/port/path | Smoke-test target URL |

Use a dedicated test account. Do not commit credentials.

## Run

Start the Flask backend first. Then run the MCP server from the ResShare repo
root:

```bash
export RESSHARE_API_BASE_URL=http://127.0.0.1:5000
export RESSHARE_USERNAME=your-user
export RESSHARE_PASSWORD=your-password
python -m mcp_server.server
```

By default the MCP endpoint is:

```text
http://127.0.0.1:8126/mcp
```

MCP client configuration example:

```json
{
  "tool_config": {
    "enabled": true,
    "mcp_servers": [
      {
        "name": "reshare",
        "url": "http://127.0.0.1:8126/mcp",
        "timeout_ms": 120000
      }
    ]
  }
}
```

## Exposed Tools

| Tool | Description |
| --- | --- |
| `get_auth_status` | Whether the configured ResShare session is authenticated |
| `list_files` | User file tree plus shared-item summary |
| `list_shared_items` | Items shared with the configured user |
| `ask_documents` | RAG Q&A over uploaded documents |
| `get_chat_stats` | Per-user vector-store stats |
| `create_folder` | Create a folder under an owned path |
| `upload_file` | Upload a local PDF, DOCX, or TXT file |
| `share_file` | Share an owned path with another username |

All tools return a JSON object with `ok`, `message`, and optional `data` /
`sources`.

## Smoke Test

With both the Flask backend and MCP HTTP server running:

```bash
python scripts/mcp_smoke.py
```

The smoke test verifies account readiness, connects to the Streamable HTTP MCP
endpoint, lists tools, and calls `get_auth_status`.

## Unit Tests

```bash
python -m unittest tests.test_mcp_server -v
```

Tests mock HTTP calls and do not require a live backend.

## Limitations

- Single configured ResShare user per MCP server process.
- Session-cookie auth to the Flask API.
- No public OAuth or per-request user delegation yet.
- Upload reads paths from the machine running the MCP server.
