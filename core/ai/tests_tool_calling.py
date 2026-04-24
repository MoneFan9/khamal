import unittest
from unittest.mock import patch, MagicMock
from core.ai.client import OllamaClient
from core.ai.rag import RCAPromptBuilder
from core.ai.tools import get_available_tools, PROPOSE_FIX_TOOL

class TestToolCalling(unittest.TestCase):
    def setUp(self):
        self.client = OllamaClient(base_url="http://test-ollama:11434")
        self.builder = RCAPromptBuilder(enable_tools=True)

    @patch("requests.post")
    def test_ollama_client_chat_with_tools(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"role": "assistant", "content": "I'll use a tool."}}
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "Help me."}]
        tools = get_available_tools()

        self.client.chat(model="llama3", messages=messages, tools=tools)

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["tools"], tools)

    def test_rca_prompt_builder_with_tools(self):
        logs = ["ERROR: Something broke"]
        prompt = self.builder.build_prompt(logs)

        self.assertIn("propose_fix", prompt.system)
        self.assertTrue(self.builder.enable_tools)

    def test_tools_definition(self):
        tools = get_available_tools()
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["function"]["name"], "propose_fix")
        self.assertIn("rationale", tools[0]["function"]["parameters"]["required"])
        self.assertIn("changes", tools[0]["function"]["parameters"]["required"])

if __name__ == "__main__":
    unittest.main()
