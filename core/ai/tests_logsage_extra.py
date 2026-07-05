from django.test import TestCase
from core.ai.logsage import LogSagePreprocessor

class LogSagePreprocessorTests(TestCase):
    def setUp(self):
        self.preprocessor = LogSagePreprocessor(max_output_lines=5, context_window=1)

    def test_is_noise(self):
        self.assertTrue(self.preprocessor.is_noise("heartbeat"))
        self.assertTrue(self.preprocessor.is_noise("GET /health HTTP/1.1"))
        self.assertFalse(self.preprocessor.is_noise("ERROR: Database connection failed"))

    def test_get_severity_score(self):
        self.assertEqual(self.preprocessor.get_severity_score("CRITICAL: System failure"), 100)
        self.assertEqual(self.preprocessor.get_severity_score("EXCEPTION: Null pointer"), 90)
        self.assertEqual(self.preprocessor.get_severity_score("ERROR: Something went wrong"), 80)
        self.assertEqual(self.preprocessor.get_severity_score("WARNING: Low disk space"), 40)
        self.assertEqual(self.preprocessor.get_severity_score("INFO: User logged in"), 10)
        self.assertEqual(self.preprocessor.get_severity_score("unknown log line"), 10)

    def test_deduplicate(self):
        logs = ["log1", "log2", "log2", "log3", "log1"]
        expected = ["log1", "log2", "log3", "log1"]
        self.assertEqual(self.preprocessor.deduplicate(logs), expected)

    def test_process_basic(self):
        raw_logs = "INFO: log1\nINFO: log2\nERROR: crash\nINFO: log3"
        processed = self.preprocessor.process(raw_logs)
        self.assertIn("ERROR: crash", processed)
        self.assertIn("INFO: log2", processed) # Context window
        self.assertIn("INFO: log3", processed) # Context window

    def test_process_empty(self):
        self.assertEqual(self.preprocessor.process(""), [])
        self.assertEqual(self.preprocessor.process(None), [])

    def test_prioritize_logs_limit(self):
        # max_output_lines is 5
        logs = [
            "INFO: line 1",
            "INFO: line 2",
            "CRITICAL: anchor 1",
            "INFO: line 4",
            "INFO: line 5",
            "INFO: line 6",
            "CRITICAL: anchor 2",
            "INFO: line 8",
        ]
        # Anchors: 2 (indices 2, 6)
        # Context window (1): 1, 3, 5, 7
        # Total selected would be {2, 6, 1, 3, 5, 7} = 6 lines.
        # But limit is 5.
        # Phase 1 adds anchors: {2, 6}
        # Phase 2 adds context around 2: {1, 3} (Total 4)
        # Phase 2 adds context around 6: {5} (Total 5, hits limit)
        processed = self.preprocessor.process("\n".join(logs))
        self.assertEqual(len(processed), 5)
        self.assertIn("CRITICAL: anchor 1", processed)
        self.assertIn("CRITICAL: anchor 2", processed)

    def test_mpps_recency_weight(self):
        # Test that later logs have higher priority if severity is same
        preprocessor = LogSagePreprocessor(max_output_lines=2, context_window=0)
        logs = [
            "WARNING: early",
            "WARNING: late",
            "WARNING: latest",
        ]
        # Scores: 40 + (0/3)*10=40, 40 + (1/3)*10=43.3, 40 + (2/3)*10=46.6
        processed = preprocessor.process("\n".join(logs))
        self.assertEqual(processed, ["WARNING: late", "WARNING: latest"])
