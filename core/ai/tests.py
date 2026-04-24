import unittest
from unittest.mock import patch, MagicMock
from .client import OllamaClient

class TestOllamaClient(unittest.TestCase):
    def setUp(self):
        self.client = OllamaClient(base_url="http://ollama-test:11434")

    @patch("requests.post")
    def test_generate(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Hello world"}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = self.client.generate(model="llama3", prompt="Hi")

        self.assertEqual(result["response"], "Hello world")
        mock_post.assert_called_once_with(
            "http://ollama-test:11434/api/generate",
            json={"model": "llama3", "prompt": "Hi", "stream": False}
        )

    @patch("requests.post")
    def test_chat(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Hi there!"}}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        result = self.client.chat(model="llama3", messages=messages)

        self.assertEqual(result["message"]["content"], "Hi there!")
        mock_post.assert_called_once_with(
            "http://ollama-test:11434/api/chat",
            json={"model": "llama3", "messages": messages, "stream": False}
        )

    @patch("requests.get")
    def test_list_models(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"models": []}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = self.client.list_models()

        self.assertEqual(result["models"], [])
        mock_get.assert_called_once_with("http://ollama-test:11434/api/tags")

    @patch("requests.post")
    def test_pull_model(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = self.client.pull_model(name="llama3")

        self.assertEqual(result["status"], "success")
        mock_post.assert_called_once_with(
            "http://ollama-test:11434/api/pull",
            json={"name": "llama3", "stream": False}
        )
