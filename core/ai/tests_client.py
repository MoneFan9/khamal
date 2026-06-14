import unittest
from unittest.mock import patch, MagicMock
from .client import OllamaClient

class TestOllamaClient(unittest.TestCase):
    def setUp(self):
        self.client = OllamaClient(base_url="http://test:11434")

    @patch("requests.post")
    def test_generate_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Hello"}
        mock_post.return_value = mock_response

        res = self.client.generate(
            "llama3", "Hi",
            system="sys", template="temp", context=[1,2], options={"opt": 1}
        )

        self.assertEqual(res, {"response": "Hello"})
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        json_data = kwargs["json"]
        self.assertEqual(json_data["prompt"], "Hi")
        self.assertEqual(json_data["model"], "llama3")
        self.assertEqual(json_data["system"], "sys")
        self.assertEqual(json_data["template"], "temp")
        self.assertEqual(json_data["context"], [1,2])
        self.assertEqual(json_data["options"], {"opt": 1})

    @patch("requests.post")
    def test_chat_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Hi"}}
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "Hi"}]
        res = self.client.chat("llama3", messages, tools=["t1"], options={"opt": 1})

        self.assertEqual(res["message"]["content"], "Hi")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        json_data = kwargs["json"]
        self.assertEqual(json_data["tools"], ["t1"])
        self.assertEqual(json_data["options"], {"opt": 1})

    @patch("requests.get")
    def test_list_models(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"models": []}
        mock_get.return_value = mock_response

        res = self.client.list_models()
        self.assertEqual(res, {"models": []})

    @patch("requests.post")
    def test_pull_model(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_post.return_value = mock_response

        res = self.client.pull_model("llama3")
        self.assertEqual(res, {"status": "success"})

    @patch("requests.post")
    def test_show_model(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"details": {}}
        mock_post.return_value = mock_response

        res = self.client.show_model("llama3")
        self.assertEqual(res, {"details": {}})

    @patch("requests.post")
    def test_unload_model(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        self.client.unload_model("llama3")
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["keep_alive"], 0)

    @patch("requests.post")
    def test_session_context_manager(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        with self.client.session("llama3") as session:
            self.assertEqual(session, self.client)

        # Verify unload was called
        mock_post.assert_called_with("http://test:11434/api/generate", json={"model": "llama3", "keep_alive": 0})

    @patch("requests.post")
    def test_session_context_manager_exception(self, mock_post):
        mock_post.side_effect = Exception("Unload failed")

        try:
            with self.client.session("llama3") as session:
                pass
        except Exception:
            self.fail("session context manager should suppress unload exceptions")

    @patch("requests.post")
    def test_generate_stream(self, mock_post):
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [b'{"response": "H"}', b'{"response": "i"}']
        mock_post.return_value = mock_response

        res = self.client.generate("llama3", "Hi", stream=True)
        lines = list(res)
        self.assertEqual(len(lines), 2)
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_generate_keep_alive(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        self.client.generate("llama3", "Hi", keep_alive="10m")
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["keep_alive"], "10m")

    @patch("requests.post")
    def test_chat_stream(self, mock_post):
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [b'{"message": {"content": "H"}}', b'{"message": {"content": "i"}}']
        mock_post.return_value = mock_response

        res = self.client.chat("llama3", [{"role": "user", "content": "Hi"}], stream=True)
        lines = list(res)
        self.assertEqual(len(lines), 2)
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_pull_model_stream(self, mock_post):
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [b'{"status": "downloading"}', b'{"status": "success"}']
        mock_post.return_value = mock_response

        res = self.client.pull_model("llama3", stream=True)
        lines = list(res)
        self.assertEqual(len(lines), 2)
        mock_post.assert_called_once()
