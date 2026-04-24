import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from .client import OllamaClient
from .executor import apply_fix

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

    @patch("requests.post")
    def test_unload_model(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = self.client.unload_model(model="llama3")

        self.assertEqual(result["status"], "success")
        mock_post.assert_called_once_with(
            "http://ollama-test:11434/api/generate",
            json={"model": "llama3", "keep_alive": 0}
        )

class TestExecutor(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_apply_fix_create(self):
        fix_data = {
            "rationale": "Test create",
            "changes": [
                {
                    "file_path": "new_file.py",
                    "action": "create",
                    "content": "print('hello')"
                }
            ]
        }
        results = apply_fix(fix_data, root_dir=self.test_dir)
        self.assertEqual(results, ["Created new_file.py"])
        self.assertTrue((self.test_dir / "new_file.py").exists())
        self.assertEqual((self.test_dir / "new_file.py").read_text(), "print('hello')")

    def test_apply_fix_update_full(self):
        file_path = self.test_dir / "update_file.py"
        file_path.write_text("old content")

        fix_data = {
            "rationale": "Test update full",
            "changes": [
                {
                    "file_path": "update_file.py",
                    "action": "update",
                    "content": "new content"
                }
            ]
        }
        results = apply_fix(fix_data, root_dir=self.test_dir)
        self.assertEqual(results, ["Updated update_file.py"])
        self.assertEqual(file_path.read_text(), "new content")

    def test_apply_fix_update_block(self):
        file_path = self.test_dir / "block_file.py"
        file_path.write_text("line1\nline2\nline3")

        fix_data = {
            "rationale": "Test update block",
            "changes": [
                {
                    "file_path": "block_file.py",
                    "action": "update",
                    "search_block": "line2",
                    "content": "REPLACED"
                }
            ]
        }
        results = apply_fix(fix_data, root_dir=self.test_dir)
        self.assertEqual(results, ["Updated block_file.py"])
        self.assertEqual(file_path.read_text(), "line1\nREPLACED\nline3")

    def test_apply_fix_delete(self):
        file_path = self.test_dir / "delete_me.py"
        file_path.write_text("content")

        fix_data = {
            "rationale": "Test delete",
            "changes": [
                {
                    "file_path": "delete_me.py",
                    "action": "delete",
                    "content": ""
                }
            ]
        }
        results = apply_fix(fix_data, root_dir=self.test_dir)
        self.assertEqual(results, ["Deleted delete_me.py"])
        self.assertFalse(file_path.exists())

    def test_apply_fix_security_traversal(self):
        fix_data = {
            "rationale": "Test security",
            "changes": [
                {
                    "file_path": "../outside.py",
                    "action": "create",
                    "content": "danger"
                }
            ]
        }
        with self.assertRaises(PermissionError):
            apply_fix(fix_data, root_dir=self.test_dir)
