import unittest
from core.ai.rag import RCAPromptBuilder

class TestPromptsQuality(unittest.TestCase):
    def setUp(self):
        self.builder = RCAPromptBuilder(enable_tools=True)

    def test_system_prompt_contains_new_guidelines(self):
        system_prompt = self.builder.system_prompt

        self.assertIn("Chain-of-Thought", system_prompt)
        self.assertIn("Anti-Hallucination Protocol", system_prompt)
        self.assertIn("Resource exhaustion", system_prompt)
        self.assertIn("Deterministic JSON", system_prompt)
        self.assertIn("'search_block' Rule", system_prompt)

    def test_user_template_contains_new_structure(self):
        logs = ["ERROR: Database connection failed"]
        prompt = self.builder.build_prompt(logs)
        user_content = prompt.user

        self.assertIn("Technical Deep Dive", user_content)
        self.assertIn("Chronological Events", user_content)
        self.assertIn("Strict Constraint", user_content)
        self.assertIn("Problem Summary", user_content)

    def test_tool_descriptions_are_refined(self):
        from core.ai.tools import PROPOSE_FIX_TOOL
        desc = PROPOSE_FIX_TOOL["function"]["description"]
        self.assertIn("precision-engineered", desc)
        self.assertIn("bypasses human approval", desc)

        params = PROPOSE_FIX_TOOL["function"]["parameters"]["properties"]
        self.assertIn("high-density technical justification", params["rationale"]["description"])
        self.assertIn("Absolute-style relative path", params["changes"]["items"]["properties"]["file_path"]["description"])

if __name__ == "__main__":
    unittest.main()
