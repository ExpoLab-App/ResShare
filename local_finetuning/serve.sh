#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Serve the ResShare fine-tune by default; an explicit path can select another GGUF.
model_path="${1:-$repo_root/local_finetuning/artifacts/resshare-Q4_K_M.gguf}"
if ! command -v llama-server >/dev/null; then
  echo "Install the runtime first: brew install llama.cpp" >&2
  exit 1
fi
if [[ ! -f "$model_path" ]]; then
  echo "GGUF not found: $model_path" >&2
  exit 1
fi
exec llama-server -m "$model_path" \
  --host "${LOCAL_LLM_HOST:-127.0.0.1}" --port "${LOCAL_LLM_PORT:-8081}" \
  --alias resshare-local -c 8192 -ngl 99 --parallel 1 \
  --jinja --chat-template-kwargs '{"enable_thinking":false}'
