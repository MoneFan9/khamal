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
        self.assertEqual(self.preprocessor.get_severity_score("PANIC: kernel panic"), 100)
        self.assertEqual(self.preprocessor.get_severity_score("SIGSEGV: segmentation fault"), 100)
        self.assertEqual(self.preprocessor.get_severity_score("EXCEPTION: unhandled exception"), 90)
        self.assertEqual(self.preprocessor.get_severity_score("TRACEBACK: most recent call last"), 90)
        self.assertEqual(self.preprocessor.get_severity_score("ERROR: unexpected error"), 80)
        self.assertEqual(self.preprocessor.get_severity_score("WARNING: disk almost full"), 40)
        self.assertEqual(self.preprocessor.get_severity_score("INFO: data received"), 10)

    def test_context_window_preservation(self):
        # max_output_lines is 5, context_window is 1
        self.preprocessor = LogSagePreprocessor(max_output_lines=3, context_window=1)
        logs = """
        INFO: before 1
        INFO: before 2
        ERROR: critical error
        INFO: after 1
        INFO: after 2
        """
        processed = self.preprocessor.process(logs)

        # Should prioritize the ERROR and its neighbors (before 2 and after 1)
        self.assertIn("ERROR: critical error", processed)
        self.assertIn("INFO: before 2", processed)
        self.assertIn("INFO: after 1", processed)
        self.assertNotIn("INFO: before 1", processed)
        self.assertNotIn("INFO: after 2", processed)

    def test_prioritization_when_exceeding_max_lines(self):
        # max_output_lines is 5
        # Note: with context_window=3 (default), ERRORs will boost surrounding lines.
        # In this test, all logs are within 3 lines of an ERROR.
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
        # Context preservation might change which INFO logs are kept compared to simple recency

    def test_empty_logs(self):
        self.assertEqual(self.preprocessor.process(""), [])
        self.assertEqual(self.preprocessor.process("\n\n  \n"), [])
        # Directly test _prioritize_logs for coverage of empty list check
        self.assertEqual(self.preprocessor._prioritize_logs([]), [])

    def test_quota_limits_in_context_window(self):
        # Test max_output_lines limit in _add_context_window
        self.preprocessor = LogSagePreprocessor(max_output_lines=2, context_window=1)
        logs = """
        ERROR: error 1
        INFO: context for 1
        ERROR: error 2
        """
        processed = self.preprocessor.process(logs)
        # error 1 and error 2 should be added as anchors first.
        # Then context for 1 would be added but max_output_lines=2 is already reached.
        self.assertEqual(len(processed), 2)
        self.assertIn("ERROR: error 1", processed)
        self.assertIn("ERROR: error 2", processed)
        self.assertNotIn("INFO: context for 1", processed)

    def test_fill_remaining_quota(self):
        # Test _fill_remaining_quota with max_output_lines
        self.preprocessor = LogSagePreprocessor(max_output_lines=2, context_window=0)
        logs = """
        INFO: log 1
        INFO: log 2
        INFO: log 3
        """
        processed = self.preprocessor.process(logs)
        self.assertEqual(len(processed), 2)
        # Should fill with logs by priority (recency boosts them slightly)
        # log 3 and log 2 should be more recent
        self.assertIn("INFO: log 3", processed)
        self.assertIn("INFO: log 2", processed)

    def test_process_small_log_list(self):
        # Case where len(deduplicated) <= self.max_output_lines
        self.preprocessor = LogSagePreprocessor(max_output_lines=10)
        logs = "INFO: single log line"
        processed = self.preprocessor.process(logs)
        self.assertEqual(processed, ["INFO: single log line"])
