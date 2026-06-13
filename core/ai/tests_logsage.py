import unittest
from ai.logsage import LogSagePreprocessor

class TestLogSagePreprocessor(unittest.TestCase):
    def setUp(self):
        self.preprocessor = LogSagePreprocessor(max_output_lines=5, context_window=1)

    def test_is_noise(self):
        self.assertTrue(self.preprocessor.is_noise("Sending heartbeat to server"))
        self.assertTrue(self.preprocessor.is_noise("GET /health HTTP/1.1 200"))
        self.assertFalse(self.preprocessor.is_noise("Internal Server Error"))

    def test_get_severity_score(self):
        self.assertEqual(self.preprocessor.get_severity_score("CRITICAL failure"), 100)
        self.assertEqual(self.preprocessor.get_severity_score("ERROR happened"), 80)
        self.assertEqual(self.preprocessor.get_severity_score("just info"), 10)
        # Check case insensitivity for score
        self.assertEqual(self.preprocessor.get_severity_score("critical failure"), 100)

    def test_deduplicate(self):
        logs = ["error1", "error1", "error2", "error1"]
        deduped = self.preprocessor.deduplicate(logs)
        self.assertEqual(deduped, ["error1", "error2", "error1"])

    def test_process_small_log(self):
        raw_logs = "line1\nline2\nline3"
        processed = self.preprocessor.process(raw_logs)
        self.assertEqual(processed, ["line1", "line2", "line3"])

    def test_process_with_prioritization(self):
        # max_output_lines = 5, context_window = 1
        raw_logs = (
            "info1\n"         # 0
            "info2\n"         # 1
            "info3\n"         # 2
            "CRITICAL error\n" # 3 (Anchor)
            "info4\n"         # 4 (Context of 3)
            "info5\n"         # 5
            "ERROR alert\n"   # 6 (Anchor)
            "info6\n"         # 7 (Context of 6)
            "info7\n"         # 8
            "info8"           # 9
        )
        processed = self.preprocessor.process(raw_logs)

        # Should have anchors (3, 6) and their context (2, 4, 5, 7)
        # 3 is critical (score 100), 6 is error (score 80)
        # Quota is 5.
        # Phase 1 (Anchors): Adds 3 and 6. (Count: 2)
        # Phase 2 (Context):
        #   For 3: Add 2 and 4. (Count: 4)
        #   For 6: Add 5. (Count: 5) -> REACHED QUOTA

        self.assertIn("CRITICAL error", processed)
        self.assertIn("ERROR alert", processed)
        self.assertEqual(len(processed), 5)
        # Verify chronological order
        self.assertEqual(processed, ["info3", "CRITICAL error", "info4", "info5", "ERROR alert"])

    def test_process_fill_remaining(self):
        self.preprocessor.max_output_lines = 10
        raw_logs = "info1\nERROR anchor\ninfo2\ninfo3"
        processed = self.preprocessor.process(raw_logs)
        # Anchor: ERROR anchor (score 80)
        # Context: info1, info2
        # Remaining: info3
        # Should have all since quota is 10
        self.assertEqual(len(processed), 4)
        self.assertEqual(processed, ["info1", "ERROR anchor", "info2", "info3"])

    def test_noise_filtering(self):
        raw_logs = "info\nheartbeat\nERROR"
        processed = self.preprocessor.process(raw_logs)
        self.assertEqual(processed, ["info", "ERROR"])

    def test_empty_logs(self):
        self.assertEqual(self.preprocessor.process(""), [])
        self.assertEqual(self.preprocessor.process(None), [])
