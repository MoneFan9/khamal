import unittest
import tempfile
import shutil
from pathlib import Path
from core.ai.logsage import LogSagePreprocessor
from core.ai.rag import RCAPromptBuilder
from core.ai.chaos_simulations import ChaosGenerator

class TestChaosReal(unittest.TestCase):
    """
    Continuous Verification of LogSage against LIVE failure simulations.
    These tests execute actual Python scripts that fail to ensure LogSage
    can process authentic, noisy log streams.
    """

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.preprocessor = LogSagePreprocessor(max_output_lines=100)
        self.builder = RCAPromptBuilder(enable_tools=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _verify_scenario(self, scenario_func, expected_error_snippet):
        """Helper to run a real chaos scenario and verify prompt density."""
        # 1. Run simulation to get REAL logs
        scenario = scenario_func(real=True)
        raw_logs = scenario["logs"]

        # 2. Preprocess logs
        processed_logs = self.preprocessor.process(raw_logs)

        # 3. Build RCA Prompt
        prompt = self.builder.build_prompt(processed_logs, scenario["project_context"])

        # 4. Assertions: Ensure the 'smoking gun' is in the prompt
        self.assertIn(expected_error_snippet, prompt.user)
        self.assertIn(scenario["project_context"]["project_name"], prompt.user)

        # Verify severity detection
        max_severity = max(self.preprocessor.get_severity_score(line) for line in processed_logs)
        self.assertGreaterEqual(max_severity, 80, "No critical error detected in processed logs")

    def test_real_db_failure(self):
        self._verify_scenario(
            ChaosGenerator.get_db_failure,
            "psycopg2.OperationalError"
        )

    def test_real_port_conflict(self):
        self._verify_scenario(
            ChaosGenerator.get_port_conflict,
            "Address already in use"
        )

    def test_real_syntax_error(self):
        self._verify_scenario(
            ChaosGenerator.get_syntax_error,
            "SyntaxError"
        )
