# Local Development

This guide runs each ResShare service separately so you can inspect and restart
individual processes without running the full application stack in Docker.
Keep each long-running command open in its own terminal.

## Services

The local stack consists of:

1. IPFS for file storage
2. IPFS Cluster for the storage API used by the backend
3. Qdrant for persistent RAG vectors
4. Flask for the backend API
5. React for the frontend

With `STORAGE_TYPE=memory`, no local ResilientDB server is required. To use
ResilientDB metadata storage, you need a reachable ResilientDB KV service.

## One-time setup

Install the project dependencies described in the [README](README.md), then
initialize the local IPFS repositories:

```bash
cp env.example .env
ipfs init
ipfs-cluster-service init --consensus crdt
```

Set at least these values in `.env`:

```dotenv
GOOGLE_API_KEY=your-gemini-api-key-here
FLASK_ENV=development
STORAGE_TYPE=memory
```

For ResilientDB-backed metadata instead of process-local memory, use:

```dotenv
STORAGE_TYPE=resilientdb
KV_SERVICE_URL=https://your-kv-service.example.com
```

## Start the local stack

Start the services in this order.

### Terminal 1: IPFS

```bash
ipfs daemon
```

Wait until IPFS reports that the daemon is ready before starting IPFS Cluster.

### Terminal 2: IPFS Cluster

```bash
ipfs-cluster-service daemon
```

### Terminal 3: Qdrant

```bash
docker compose up qdrant
```

Qdrant is published only on `127.0.0.1:6333`. Its collections and indexes are
persisted in the `qdrant_data` Docker volume.

### Terminal 4: Flask backend

From the repository root:

```bash
source .venv/bin/activate
set -a
source .env
set +a
python app.py
```

The backend runs at `http://localhost:5000`. When it runs directly on the host,
its default Qdrant connection is `localhost:6333`. Its IPFS Cluster and gateway
endpoints are configured in `backend/config/ipfs.config`.

### Terminal 5: React frontend

```bash
cd frontend
npm start
```

The frontend runs at `http://localhost:3000` and defaults to the backend at
`http://localhost:5000`.

## Verify the services

| Process | Address | Quick check |
|---------|---------|-------------|
| IPFS API | `127.0.0.1:5001` | `ipfs id` |
| IPFS gateway | `127.0.0.1:8080` | `curl -I http://127.0.0.1:8080/` |
| IPFS Cluster API | `127.0.0.1:9094` | `curl http://127.0.0.1:9094/api/v0/id` |
| Qdrant | `127.0.0.1:6333` | `curl http://127.0.0.1:6333/healthz` |
| Flask backend | `localhost:5000` | `curl http://localhost:5000/` |
| React frontend | `localhost:3000` | Open `http://localhost:3000` |

## Stop the stack

Stop each foreground process with `Ctrl+C`. Qdrant data remains in its Docker
volume when the container stops.

To stop the Qdrant Compose service from another terminal:

```bash
docker compose stop qdrant
```

Do not use `docker compose down -v` unless you intentionally want to delete all
Compose-managed data, including the Qdrant vector collection.

## Full Docker alternative

To run the backend, IPFS services, and Qdrant together in containers instead:

```bash
docker compose up --build
```

The React development server remains a separate process:

```bash
cd frontend
npm start
```
