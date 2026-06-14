import unittest
from .logsage import LogSagePreprocessor

class TestLogSagePreprocessor(unittest.TestCase):
    def setUp(self):
        self.processor = LogSagePreprocessor(max_output_lines=5, context_window=1)

    def test_is_noise(self):
        self.assertTrue(self.processor.is_noise("heartbeat"))
        self.assertTrue(self.processor.is_noise("GET /health"))
        self.assertFalse(self.processor.is_noise("ERROR: something broke"))

    def test_get_severity_score(self):
        self.assertEqual(self.processor.get_severity_score("CRITICAL failure"), 100)
        self.assertEqual(self.processor.get_severity_score("EXCEPTION occurred"), 90)
        self.assertEqual(self.processor.get_severity_score("Just some info"), 10)

    def test_deduplicate(self):
        logs = ["line1", "line1", "line2", "line1"]
        deduped = self.processor.deduplicate(logs)
        self.assertEqual(deduped, ["line1", "line2", "line1"])

    def test_process_basic(self):
        raw_logs = "INFO: start\nheartbeat\nERROR: crash\nINFO: end"
        result = self.processor.process(raw_logs)
        self.assertIn("ERROR: crash", result)
        self.assertNotIn("heartbeat", result)
        self.assertIn("INFO: start", result)

    def test_prioritization_logic(self):
        # max_output_lines=5, context_window=1
        logs = [
            "INFO 1",
            "INFO 2",
            "INFO 3",
            "CRITICAL ERROR",
            "INFO 5",
            "INFO 6",
            "INFO 7",
            "INFO 8"
        ]
        raw_logs = "\n".join(logs)
        result = self.processor.process(raw_logs)

        # Result should contain CRITICAL ERROR and its context (INFO 3, INFO 5)
        # Plus other lines to fill up to 5
        self.assertEqual(len(result), 5)
        self.assertIn("CRITICAL ERROR", result)
        self.assertIn("INFO 3", result)
        self.assertIn("INFO 5", result)
        # Prioritization also favors recency for remaining quota
        self.assertIn("INFO 8", result)

    def test_empty_logs(self):
        self.assertEqual(self.processor.process(""), [])
        self.assertEqual(self.processor.process(None), [])

    def test_all_noise(self):
        raw_logs = "heartbeat\nhealthcheck"
        self.assertEqual(self.processor.process(raw_logs), [])

    def test_context_window_limit(self):
        # Test the case where context window fills up the quota
        self.processor = LogSagePreprocessor(max_output_lines=2, context_window=1)
        logs = [
            "INFO 1",
            "CRITICAL ERROR",
            "INFO 3",
            "INFO 4"
        ]
        result = self.processor.process("\n".join(logs))
        # Quota is 2, so it should only have CRITICAL ERROR and one context line
        self.assertEqual(len(result), 2)

    def test_deduplicate_generator_edge_case(self):
        # Test process with many duplicate lines to trigger generator logic
        raw_logs = "\n".join(["heartbeat"] * 200)
        # It's all noise anyway
        self.assertEqual(self.processor.process(raw_logs), [])

    def test_deduplicate_identical_consecutive(self):
        # Test deduplicate method specifically
        logs = ["a", "b", "b", "c", "c", "c", "a"]
        self.assertEqual(self.processor.deduplicate(logs), ["a", "b", "c", "a"])
