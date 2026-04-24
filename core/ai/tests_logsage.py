import unittest
from .logsage import LogSagePreprocessor

class TestLogSagePreprocessor(unittest.TestCase):
    def setUp(self):
        self.preprocessor = LogSagePreprocessor(max_output_lines=5)

    def test_noise_filtering(self):
        logs = """
        INFO: Service started
        DEBUG: Heartbeat sent
        GET /health status 200
        ERROR: Connection failed
        INFO: Healthcheck ok
        """
        processed = self.preprocessor.process(logs)

        self.assertIn("INFO: Service started", processed)
        self.assertIn("ERROR: Connection failed", processed)
        self.assertNotIn("DEBUG: Heartbeat sent", processed)
        self.assertNotIn("GET /health status 200", processed)
        self.assertNotIn("INFO: Healthcheck ok", processed)

    def test_deduplication(self):
        logs = [
            "ERROR: DB connection timeout",
            "ERROR: DB connection timeout",
            "INFO: Retrying...",
            "ERROR: DB connection timeout",
        ]
        deduplicated = self.preprocessor.deduplicate(logs)
        self.assertEqual(len(deduplicated), 3)
        self.assertEqual(deduplicated[0], "ERROR: DB connection timeout")
        self.assertEqual(deduplicated[1], "INFO: Retrying...")
        self.assertEqual(deduplicated[2], "ERROR: DB connection timeout")

    def test_severity_scoring(self):
        self.assertEqual(self.preprocessor.get_severity_score("CRITICAL: Out of memory"), 100)
        self.assertEqual(self.preprocessor.get_severity_score("ERROR: unexpected error"), 80)
        self.assertEqual(self.preprocessor.get_severity_score("WARNING: disk almost full"), 40)
        self.assertEqual(self.preprocessor.get_severity_score("INFO: data received"), 10)

    def test_prioritization_when_exceeding_max_lines(self):
        # max_output_lines is 5
        logs = """
        INFO: log 1
        ERROR: critical error 1
        INFO: log 2
        INFO: log 3
        CRITICAL: fatal error 2
        INFO: log 4
        ERROR: critical error 3
        INFO: log 5
        """
        processed = self.preprocessor.process(logs)

        self.assertEqual(len(processed), 5)
        # Should contain all ERROR and CRITICAL logs
        self.assertIn("ERROR: critical error 1", processed)
        self.assertIn("CRITICAL: fatal error 2", processed)
        self.assertIn("ERROR: critical error 3", processed)
        # And some INFO logs (likely the most recent ones due to recency bonus)
        self.assertIn("INFO: log 5", processed)

    def test_empty_logs(self):
        self.assertEqual(self.preprocessor.process(""), [])
        self.assertEqual(self.preprocessor.process("\n\n  \n"), [])
