import unittest
from .rag import RCAPromptBuilder, RCAPrompt

class TestRCAPromptBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = RCAPromptBuilder()

    def test_build_prompt_basic(self):
        logs = ["ERROR: Connection refused", "INFO: Retrying..."]
        prompt_obj = self.builder.build_prompt(logs)

        self.assertIsInstance(prompt_obj, RCAPrompt)
        self.assertIn("### Context", prompt_obj.user)
        self.assertIn("ERROR: Connection refused", prompt_obj.user)
        self.assertIn("**Project**: Unknown", prompt_obj.user)
        self.assertEqual(prompt_obj.system, self.builder.SYSTEM_PROMPT)

    def test_to_ollama_messages(self):
        logs = ["ERROR: Fail"]
        prompt_obj = self.builder.build_prompt(logs)
        messages = prompt_obj.to_ollama_messages()

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[0]["content"], prompt_obj.system)
        self.assertEqual(messages[1]["content"], prompt_obj.user)

    def test_build_prompt_with_context(self):
        logs = ["ERROR: Syntax error"]
        context = {
            "project_name": "MyCoolApp",
            "language": "Django/Python",
            "environment": "Development",
            "ignored_key": "ShouldNotBeHere"
        }
        prompt_obj = self.builder.build_prompt(logs, project_context=context)

        self.assertIn("**Project**: MyCoolApp", prompt_obj.user)
        self.assertIn("**Language/Framework**: Django/Python", prompt_obj.user)
        self.assertIn("**Environment**: Development", prompt_obj.user)
        self.assertNotIn("ignored_key", prompt_obj.user)

    def test_empty_logs_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.builder.build_prompt([])

    def test_invalid_logs_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.builder.build_prompt([None])

    def test_truncation(self):
        short_builder = RCAPromptBuilder(max_log_chars=10)
        logs = ["This is a long log line"]
        prompt_obj = short_builder.build_prompt(logs)

        self.assertIn("[truncated", prompt_obj.user)
        # It should keep the end of the log
        self.assertTrue(prompt_obj.user.endswith("g log line\n```\n"))

    def test_custom_template(self):
        custom_template = "PROJECT: {project_name} LOGS: {logs}"
        builder = RCAPromptBuilder(rca_template=custom_template)
        logs = ["log1"]
        prompt_obj = builder.build_prompt(logs, project_context={"project_name": "Test"})

        self.assertEqual(prompt_obj.user, "PROJECT: Test LOGS: log1")

    def test_repr(self):
        self.assertIn("RCAPromptBuilder", repr(self.builder))
        self.assertIn("max_log_chars=12000", repr(self.builder))
