import unittest
from unittest.mock import Mock, patch

import requests

from backend.services.answer_service import GenerationError, LocalGenerationClient


def chunk(filename, text):
    return {"chunk": {"metadata": {"filename": filename}, "text": text}, "score": 0.9}


class LocalGenerationClientTest(unittest.TestCase):
    def test_empty_context_skips_the_model(self):
        client = LocalGenerationClient(generation_model="llama3.2", base_url="http://127.0.0.1:11434/v1")

        with patch("backend.services.answer_service.requests.post") as post:
            answer = client.generate_answer("What is this?", [])

        post.assert_not_called()
        self.assertIn("couldn't find", answer)

    def test_generate_answer_reads_chat_completion_content(self):
        client = LocalGenerationClient(
            generation_model="llama3.2",
            base_url="http://127.0.0.1:11434/v1/",
        )
        response = Mock()
        response.json.return_value = {
            "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": "  Payment is due in 30 days.  "}}]
        }
        response.raise_for_status.return_value = None

        with patch("backend.services.answer_service.requests.post", return_value=response) as post:
            answer = client.generate_answer("When is payment due?", [chunk("contract.pdf", "Net 30.")])

        self.assertEqual(answer, "Payment is due in 30 days.")
        self.assertEqual(post.call_args.args[0], "http://127.0.0.1:11434/v1/chat/completions")
        body = post.call_args.kwargs["json"]
        self.assertEqual(body["model"], "llama3.2")
        self.assertFalse(body["stream"])
        self.assertEqual(body["messages"][0]["role"], "system")
        self.assertIn("contract.pdf", body["messages"][1]["content"])
        self.assertIn("Net 30.", body["messages"][1]["content"])
        self.assertEqual(post.call_args.kwargs["headers"]["Content-Type"], "application/json")

    def test_connection_error_raises_generation_error(self):
        client = LocalGenerationClient(generation_model="llama3.2", base_url="http://127.0.0.1:11434/v1")

        with patch(
            "backend.services.answer_service.requests.post",
            side_effect=requests.exceptions.ConnectionError("refused"),
        ):
            with self.assertRaises(GenerationError):
                client.generate_answer("Hello?", [chunk("notes.txt", "hello")])


    def test_missing_model_raises_generation_error(self):
        client = LocalGenerationClient(generation_model="missing-model", base_url="http://127.0.0.1:11434/v1")
        response = Mock()
        response.status_code = 404
        error = requests.exceptions.HTTPError("not found")
        error.response = response

        with patch("backend.services.answer_service.requests.post", side_effect=error):
            with self.assertRaises(GenerationError):
                client.generate_answer("Hello?", [chunk("notes.txt", "hello")])


    def test_explicit_timeout_overrides_environment(self):
        with patch.dict("os.environ", {"LOCAL_LLM_TIMEOUT": "99"}):
            client = LocalGenerationClient(timeout=7)
        self.assertEqual(client.timeout, 7)

    def test_nonpositive_timeout_is_rejected(self):
        with self.assertRaises(ValueError):
            LocalGenerationClient(timeout=0)
