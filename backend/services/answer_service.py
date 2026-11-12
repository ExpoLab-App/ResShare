import os
from typing import Dict, List

import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_LOCAL_LLM_BASE_URL = "http://127.0.0.1:11434/v1"
DEFAULT_LOCAL_LLM_MODEL = "llama3.2"


class LocalGenerationClient:
    """Chat completion client for a local OpenAI-compatible server.

    Ollama, LM Studio, llama.cpp, and vLLM all expose this API. Point
    LOCAL_LLM_BASE_URL at the server and LOCAL_LLM_MODEL at an installed model.
    """

    def __init__(
        self,
        generation_model: str | None = None,
        base_url: str | None = None,
        timeout: int = 120,
    ):
        self.model_name = generation_model or os.getenv("LOCAL_LLM_MODEL", DEFAULT_LOCAL_LLM_MODEL)
        self.base_url = (base_url or os.getenv("LOCAL_LLM_BASE_URL", DEFAULT_LOCAL_LLM_BASE_URL)).rstrip("/")
        self.timeout = timeout
        self.url = f"{self.base_url}/chat/completions"

    def generate_answer(
            self,
            query: str,
            context_chunks: List[Dict],
            max_tokens: int = 5000
        ) -> str:
        """
        Generate an answer using retrieved context.

        Args:
            query: User's question
            context_chunks: Retrieved relevant chunks
            max_tokens: Maximum tokens for response

        Returns:
            Generated answer
        """
        if not context_chunks:
            return "I couldn't find any relevant information in your uploaded files to answer this question."

        try:
            data = self._build_body(context_chunks, query, max_tokens)

            response = requests.post(
                self.url,
                headers={"Content-Type": "application/json"},
                json=data,
                timeout=self.timeout,
            )
            response.raise_for_status()

            result = response.json()
            logger.debug(f"Local LLM response: {result}")
            content = result["choices"][0]["message"]["content"]
            if not content or not content.strip():
                return "The local model returned an empty response. Please try again."
            return content.strip()

        except requests.exceptions.ConnectionError:
            logger.error(f"Could not reach the local LLM at {self.url}")
            return "I couldn't reach the local language model. Make sure it is running and try again."
        except requests.exceptions.Timeout:
            logger.error(f"Local LLM request timed out after {self.timeout}s ({self.url})")
            return "The local language model took too long to respond. Please try again."
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error(f"Local LLM request failed ({status}): {e}")
            if status == 404:
                return (
                    f"The local model '{self.model_name}' is not available. "
                    "Install it or set LOCAL_LLM_MODEL to a model you already have."
                )
            return "I encountered an error while generating the response. Please try again."
        except Exception as e:
            logger.error(f"Failed to generate LLM response: {e}")
            return "I encountered an error while generating the response. Please try again."

    def _build_body(self, context_chunks: List[Dict], query: str, max_tokens: int):
        return {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on the provided context from user's documents.",
                },
                {
                    "role": "user",
                    "content": self._build_prompt(context_chunks, query),
                },
            ],
            "max_tokens": max_tokens,
            "temperature": 0.2,
            "stream": False,
        }

    @staticmethod
    def _build_prompt(context_chunks: List[Dict], query: str):
        context_text = "\n\n".join([
                    f"From {chunk['chunk']['metadata']['filename']}:\n{chunk['chunk']['text']}"
                    for chunk in context_chunks[:3]
                ])
        return f"""
        Based on the following context from the user's uploaded files, please answer their question.
        If the context doesn't contain enough information to answer the question, always say so.

        Context: {context_text}

        Question: {query}

        Answer:
        """
