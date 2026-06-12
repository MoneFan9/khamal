import unittest
from unittest.mock import patch, MagicMock
from .client import OllamaClient

class TestOllamaClient(unittest.TestCase):
    def setUp(self):
        # We use a dummy URL to avoid real requests
        self.client = OllamaClient(base_url="http://ollama-test:11434")

    @patch("requests.post")
    def test_generate_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Hello"}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = self.client.generate("llama3", "Hi")

        self.assertEqual(result["response"], "Hello")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("/api/generate", args[0])
        self.assertEqual(kwargs["json"]["model"], "llama3")
        self.assertEqual(kwargs["json"]["prompt"], "Hi")

    @patch("requests.post")
    def test_chat_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"role": "assistant", "content": "Hi there"}}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        result = self.client.chat("llama3", messages)

        self.assertEqual(result["message"]["content"], "Hi there")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("/api/chat", args[0])
        self.assertEqual(kwargs["json"]["messages"], messages)

    @patch("requests.get")
    def test_list_models(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"models": [{"name": "llama3"}]}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = self.client.list_models()
        self.assertEqual(len(result["models"]), 1)
        self.assertEqual(result["models"][0]["name"], "llama3")

    @patch("requests.post")
    def test_pull_model(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = self.client.pull_model("llama3")
        self.assertEqual(result["status"], "success")

    @patch("requests.post")
    def test_unload_model(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        self.client.unload_model("llama3")
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["keep_alive"], 0)

    @patch("requests.post")
    def test_session_context_manager(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        with self.client.session("llama3") as session:
            self.assertEqual(session, self.client)

        # Verify unload was called
        self.assertTrue(mock_post.called)
        # Last call should be unload (keep_alive=0)
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["keep_alive"], 0)
