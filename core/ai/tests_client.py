import unittest
from unittest.mock import patch, MagicMock
from ai.client import OllamaClient
import requests

class TestOllamaClient(unittest.TestCase):
    def setUp(self):
        self.client = OllamaClient(base_url="http://ollama:11434")

    @patch("requests.post")
    def test_generate(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "hello"}
        mock_post.return_value = mock_response

        res = self.client.generate(
            "llama3", "hi",
            system="you are a bot",
            template="templ",
            context=[1,2,3],
            options={"temp": 0}
        )

        self.assertEqual(res["response"], "hello")
        mock_post.assert_called_once()
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["model"], "llama3")
        self.assertEqual(payload["system"], "you are a bot")
        self.assertEqual(payload["template"], "templ")
        self.assertEqual(payload["context"], [1,2,3])
        self.assertEqual(payload["options"], {"temp": 0})

    @patch("requests.post")
    def test_chat(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "hi"}}
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "hello"}]
        res = self.client.chat("llama3", messages, tools=["tool1"], options={"temp": 0})

        self.assertEqual(res["message"]["content"], "hi")
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["messages"], messages)
        self.assertEqual(payload["tools"], ["tool1"])
        self.assertEqual(payload["options"], {"temp": 0})

    @patch("requests.post")
    def test_chat_stream(self, mock_post):
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [b'line1']
        mock_post.return_value = mock_response

        res = self.client.chat("llama3", [{"role": "user", "content": "hi"}], stream=True)
        self.assertEqual(list(res), [b'line1'])

    @patch("requests.get")
    def test_list_models(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"models": []}
        mock_get.return_value = mock_response

        res = self.client.list_models()
        self.assertEqual(res["models"], [])

    @patch("requests.post")
    def test_pull_model(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_post.return_value = mock_response

        res = self.client.pull_model("llama3")
        self.assertEqual(res["status"], "success")

    @patch("requests.post")
    def test_pull_model_stream(self, mock_post):
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [b'pulling']
        mock_post.return_value = mock_response

        res = self.client.pull_model("llama3", stream=True)
        self.assertEqual(list(res), [b'pulling'])

    @patch("requests.post")
    def test_show_model(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"details": {}}
        mock_post.return_value = mock_response

        res = self.client.show_model("llama3")
        self.assertEqual(res["details"], {})

    @patch("requests.post")
    def test_unload_model(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "unloaded"}
        mock_post.return_value = mock_response

        res = self.client.unload_model("llama3")
        self.assertEqual(res["status"], "unloaded")
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["keep_alive"], 0)

    @patch("requests.post")
    def test_session_context_manager(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        with self.client.session("llama3") as session:
            self.assertEqual(session, self.client)

        # Ensure unload_model was called at the end
        self.assertTrue(any(call[1]['json'].get('keep_alive') == 0 for call in mock_post.call_args_list))

    @patch("requests.post")
    def test_session_context_manager_exception(self, mock_post):
        # First call for generate, second for unload_model (which fails)
        mock_post.side_effect = [MagicMock(), Exception("unloading failed")]

        try:
            with self.client.session("llama3"):
                pass
        except Exception:
             self.fail("session raised exception even if it should have been caught")

    @patch("requests.post")
    def test_generate_stream(self, mock_post):
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [b'line1', b'line2']
        mock_post.return_value = mock_response

        res = self.client.generate("llama3", "hi", stream=True)
        self.assertEqual(list(res), [b'line1', b'line2'])
