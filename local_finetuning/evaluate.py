"""Evaluate fixed supplied contexts against a running local chat endpoint."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlparse

from local_finetuning.prompts import ABSTENTION, PROMPT_VERSION, messages


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", required=True, help="Server model alias")
    parser.add_argument("--base-url", default="http://127.0.0.1:8081/v1")
    parser.add_argument("--artifact", required=True, help="GGUF filename plus SHA256 for provenance")
    args = parser.parse_args()
    if urlparse(args.base_url).hostname not in {"localhost", "127.0.0.1", "::1"}:
        parser.error("This evaluator only sends document context to a loopback endpoint.")
    if args.output.exists():
        parser.error("Output exists; choose a new filename.")
    records = [json.loads(line) for line in args.input.read_text().splitlines() if line.strip()]
    if not records:
        parser.error("No evaluation records.")
    import requests

    args.output.parent.mkdir(parents=True, exist_ok=True)
    failures = 0
    # Append each completed question immediately so a failure preserves evidence.
    with args.output.open("x") as handle:
        for row in records:
            start = time.monotonic()
            result = {
                "id": row["id"], "question": row["question"], "references": row["answers"],
                "answerable": row["answerable"], "model": args.model, "artifact": args.artifact,
                "prompt_version": PROMPT_VERSION,
                "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
                "human_correct": None, "human_grounded": None, "human_appropriate_abstention": None,
            }
            try:
                response = requests.post(args.base_url.rstrip("/") + "/chat/completions", json={
                    "model": args.model, "messages": messages(row["question"], row["chunks"]),
                    "temperature": 0, "max_tokens": 512,
                    "chat_template_kwargs": {"enable_thinking": False},
                }, timeout=(10, 180))
                response.raise_for_status()
                payload = response.json()
                choice = payload["choices"][0]
                answer = choice["message"]["content"]
                if not isinstance(answer, str) or not answer.strip():
                    raise ValueError("Missing or empty answer")
                if choice.get("finish_reason") != "stop":
                    raise ValueError(f"Incomplete generation: {choice.get('finish_reason')}")
                result.update(answer=answer, usage=payload.get("usage"),
                              exact_abstention=answer.strip() == ABSTENTION, error=None)
            except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
                result.update(error=str(exc))
                failures += 1
            result["seconds"] = round(time.monotonic() - start, 3)
            handle.write(json.dumps(result) + "\n")
            handle.flush()
    print(f"Saved {len(records)} results ({failures} errors). Human review is required; no automatic quality claim.")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
