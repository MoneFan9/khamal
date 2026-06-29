import unittest
from unittest.mock import patch, MagicMock
from core.ai.client import OllamaClient
import requests

class TestOllamaClient(unittest.TestCase):
    def setUp(self):
        self.client = OllamaClient(base_url="http://test-ollama:11434")

    @patch("requests.post")
    def test_generate(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "test response"}
        mock_post.return_value = mock_response

        result = self.client.generate(model="llama3", prompt="Hi", system="You are helpful", template="{prompt}", context=[1,2,3], options={"num_ctx": 4096})

        self.assertEqual(result["response"], "test response")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("/generate", args[0])
        payload = kwargs["json"]
        self.assertEqual(payload["model"], "llama3")
        self.assertEqual(payload["prompt"], "Hi")
        self.assertEqual(payload["system"], "You are helpful")
        self.assertEqual(payload["template"], "{prompt}")
        self.assertEqual(payload["context"], [1,2,3])
        self.assertEqual(payload["options"], {"num_ctx": 4096})

    @patch("requests.post")
    def test_generate_stream(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [b"line1", b"line2"]
        mock_post.return_value = mock_response

        result = self.client.generate(model="llama3", prompt="Hi", stream=True)

        self.assertEqual(list(result), [b"line1", b"line2"])

    @patch("requests.post")
    def test_chat(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "hello"}}
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "hi"}]
        result = self.client.chat(model="llama3", messages=messages, tools=[{"type": "function"}], options={"temp": 0})

        self.assertEqual(result["message"]["content"], "hello")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("/chat", args[0])
        payload = kwargs["json"]
        self.assertEqual(payload["messages"], messages)
        self.assertEqual(payload["tools"], [{"type": "function"}])

    @patch("requests.post")
    def test_chat_stream(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [b'{"message": {"content": "h"}}', b'{"message": {"content": "i"}}']
        mock_post.return_value = mock_response

        result = self.client.chat(model="llama3", messages=[], stream=True)
        self.assertEqual(list(result), [b'{"message": {"content": "h"}}', b'{"message": {"content": "i"}}'])

    @patch("requests.get")
    def test_list_models(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}
        mock_get.return_value = mock_response

        result = self.client.list_models()
        self.assertEqual(result, {"models": []})
        mock_get.assert_called_once_with("http://test-ollama:11434/api/tags")

    @patch("requests.post")
    def test_pull_model(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_post.return_value = mock_response

        result = self.client.pull_model("llama3")
        self.assertEqual(result, {"status": "success"})
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_pull_model_stream(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [b"pulling", b"done"]
        mock_post.return_value = mock_response

        result = self.client.pull_model("llama3", stream=True)
        self.assertEqual(list(result), [b"pulling", b"done"])

    @patch("requests.post")
    def test_show_model(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"modelfile": "..."}
        mock_post.return_value = mock_response

        result = self.client.show_model("llama3")
        self.assertEqual(result, {"modelfile": "..."})

    @patch("requests.post")
    def test_unload_model(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        self.client.unload_model("llama3")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["keep_alive"], 0)

    @patch("requests.post")
    def test_session_context_manager(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        with self.client.session("llama3") as client:
            self.assertEqual(client, self.client)

        # Verify unload was called
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["keep_alive"], 0)

    @patch("requests.post")
    def test_session_context_manager_exception_swallowed(self, mock_post):
        mock_post.side_effect = Exception("unload failed")

        with self.client.session("llama3"):
            pass

        mock_post.assert_called_once()
        # Should not raise exception
