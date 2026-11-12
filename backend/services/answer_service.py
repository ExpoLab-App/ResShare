"""Bounded, non-thinking chat completions against a local model server."""
import os

import requests

from backend.rag.prompts import ABSTENTION, messages


class GenerationError(RuntimeError):
    pass


class LocalGenerationClient:
    def __init__(self, generation_model: str | None = None,
                 base_url: str | None = None, timeout: float | None = None):
        self.url = (base_url or os.getenv("LOCAL_LLM_BASE_URL", "http://127.0.0.1:8081/v1")).rstrip("/") + "/chat/completions"
        self.model = generation_model or os.getenv("LOCAL_LLM_MODEL", "resshare-local")
        self.timeout = float(timeout if timeout is not None else os.getenv("LOCAL_LLM_TIMEOUT", "120"))
        if self.timeout <= 0:
            raise ValueError("LOCAL_LLM_TIMEOUT must be positive")
        # UTF-8 bytes conservatively bound text tokens without loading a second
        # tokenizer. Reserve room in an 8K window for template and output tokens.
        self.max_prompt_bytes = 6000
        self.max_output_tokens = 512

    def select_context(self, query, context_chunks):
        def size(chunks):
            evidence = [{"filename": c["chunk"]["metadata"]["filename"],
                         "text": c["chunk"]["text"]} for c in chunks]
            return sum(len(m["content"].encode("utf-8")) for m in messages(query, evidence))

        if size([]) > self.max_prompt_bytes:
            raise ValueError("Query exceeds the local model input budget")
        selected = []
        for chunk in context_chunks:
            if chunk["chunk"]["text"].strip() and size(selected + [chunk]) <= self.max_prompt_bytes:
                selected.append(chunk)
        return selected

    def generate_answer(self, query, context_chunks):
        if not context_chunks:
            return ABSTENTION
        if self.select_context(query, context_chunks) != context_chunks:
            raise ValueError("Context exceeds the local model input budget")
        evidence = [{"filename": c["chunk"]["metadata"]["filename"],
                     "text": c["chunk"]["text"]} for c in context_chunks]
        try:
            response = requests.post(self.url, headers={"Content-Type": "application/json"}, json={
                "model": self.model,
                "messages": messages(query, evidence),
                "temperature": 0,
                "max_tokens": self.max_output_tokens,
                "stream": False,
                "chat_template_kwargs": {"enable_thinking": False},
            }, timeout=self.timeout)
            response.raise_for_status()
            choice = response.json()["choices"][0]
            answer = choice["message"]["content"]
            if choice.get("finish_reason") != "stop":
                raise GenerationError("Local model did not finish its answer")
            if not isinstance(answer, str) or not answer.strip() or "<think>" in answer or "</think>" in answer:
                raise GenerationError("Local model returned an invalid direct answer")
            return answer.strip()
        except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
            raise GenerationError("Local model request failed") from exc
