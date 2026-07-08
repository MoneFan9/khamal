import unittest
from core.ai.logsage import LogSagePreprocessor

class TestLogSagePreprocessorExtra(unittest.TestCase):
    def setUp(self):
        self.preprocessor = LogSagePreprocessor(max_output_lines=5, context_window=1)

    def test_is_noise(self):
        self.assertTrue(self.preprocessor.is_noise("heartbeat: ok"))
        self.assertTrue(self.preprocessor.is_noise("GET /health HTTP/1.1 200"))
        self.assertFalse(self.preprocessor.is_noise("CRITICAL: database connection failed"))

    def test_get_severity_score(self):
        self.assertEqual(self.preprocessor.get_severity_score("CRITICAL: failure"), 100)
        self.assertEqual(self.preprocessor.get_severity_score("EXCEPTION in thread"), 90)
        self.assertEqual(self.preprocessor.get_severity_score("just some info"), 10)

    def test_deduplicate(self):
        logs = ["error 1", "error 2", "error 2", "error 3"]
        expected = ["error 1", "error 2", "error 3"]
        self.assertEqual(self.preprocessor.deduplicate(logs), expected)

    def test_process_empty(self):
        self.assertEqual(self.preprocessor.process(""), [])
        self.assertEqual(self.preprocessor.process(None), [])

    def test_prioritize_logs_strategy(self):
        # We want to see if it picks the anchor and its context
        logs = [
            "info 1",
            "info 2",
            "CRITICAL ERROR",
            "info 3",
            "info 4"
        ]
        # max_output_lines=5, context_window=1
        # Anchors: index 2
        # Context: index 1, 3
        # Fill: index 4, 0
        processed = self.preprocessor.process("\n".join(logs))
        self.assertIn("CRITICAL ERROR", processed)
        self.assertIn("info 2", processed)
        self.assertIn("info 3", processed)
        self.assertEqual(len(processed), 5)

    def test_noise_filtering_in_process(self):
        logs = "info\nheartbeat\nERROR"
        processed = self.preprocessor.process(logs)
        self.assertNotIn("heartbeat", processed)
        self.assertIn("ERROR", processed)
