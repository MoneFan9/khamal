import unittest
import tempfile
import shutil
from pathlib import Path
from core.ai.logsage import LogSagePreprocessor
from core.ai.rag import RCAPromptBuilder
from core.ai.executor import apply_fix
from core.ai.chaos_simulations import ChaosGenerator

class TestChaosEngineering(unittest.TestCase):
    """
    Chaos Engineering test suite verifying LogSage pipeline resiliency.
    Each test simulates a failure, processes logs, and applies an AI-suggested fix.
    """

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.preprocessor = LogSagePreprocessor(max_output_lines=50)
        self.builder = RCAPromptBuilder(enable_tools=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _run_chaos_pipeline(self, scenario):
        """Helper to run the full LogSage pipeline for a given chaos scenario."""
        # 1. Simulate "Broken" State
        broken_file_path = self.test_dir / scenario["broken_file"]
        broken_file_path.parent.mkdir(parents=True, exist_ok=True)
        broken_file_path.write_text(scenario["broken_content"])

        # 2. LogSage: Preprocess Logs
        processed_logs = self.preprocessor.process(scenario["logs"])
        # Verify critical info isn't filtered out
        self.assertTrue(any(self.preprocessor.get_severity_score(l) >= 80 for l in processed_logs))

        # 3. LogSage: Build RCA Prompt
        prompt = self.builder.build_prompt(processed_logs, scenario["project_context"])
        self.assertIn(scenario["project_context"]["project_name"], prompt.user)

        # 4. Mock AI Fix (This simulates the tool call LogSage would trigger)
        fix_data = {
            "rationale": scenario["rationale"],
            "changes": [
                {
                    "file_path": scenario["broken_file"],
                    "action": "update",
                    "search_block": scenario["search_block"],
                    "content": scenario["fixed_block"]
                }
            ]
        }

        # 5. LogSage: Apply Fix
        apply_fix(fix_data, root_dir=self.test_dir)

        # 6. Verify "Fixed" State
        self.assertEqual(broken_file_path.read_text(), scenario["fixed_content"])

    def test_db_failure_scenario(self):
        scenario = ChaosGenerator.get_db_failure()
        self._run_chaos_pipeline(scenario)

    def test_port_conflict_scenario(self):
        scenario = ChaosGenerator.get_port_conflict()
        self._run_chaos_pipeline(scenario)

    def test_syntax_error_scenario(self):
        scenario = ChaosGenerator.get_syntax_error()
        self._run_chaos_pipeline(scenario)

    def test_oom_error_scenario(self):
        """Tests the pipeline's ability to handle Out Of Memory errors."""
        scenario = ChaosGenerator.get_oom_error()
        self._run_chaos_pipeline(scenario)

    def test_permission_denied_scenario(self):
        """Tests the pipeline's ability to handle Permission Denied errors."""
        scenario = ChaosGenerator.get_permission_denied()
        self._run_chaos_pipeline(scenario)

    def test_dependency_conflict_scenario(self):
        """Tests the pipeline's ability to handle Dependency Conflict errors."""
        scenario = ChaosGenerator.get_dependency_conflict()
        self._run_chaos_pipeline(scenario)
