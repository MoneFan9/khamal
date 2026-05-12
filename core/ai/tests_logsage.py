import pytest
from core.ai.logsage import LogSagePreprocessor

def test_logsage_prioritization_strategy():
    preprocessor = LogSagePreprocessor(max_output_lines=10, context_window=1)

    logs = [
        "Line 0: INFO Start",
        "Line 1: INFO Process 1",
        "Line 2: INFO Process 2",
        "Line 3: ERROR Critical failure here",  # Anchor 1 (index 3)
        "Line 4: INFO Cleanup 1",
        "Line 5: INFO Idle",
        "Line 6: PANIC System collapse",         # Anchor 2 (index 6)
        "Line 7: INFO Cleanup 2",
        "Line 8: INFO Process 3",
        "Line 9: WARNING Slow response",
        "Line 10: INFO Process 4",
        "Line 11: INFO Process 5",
        "Line 12: INFO End"
    ]

    # Phase 1: Anchors (3, 6)
    # Phase 2: Context (+/- 1) -> (2, 3, 4) and (5, 6, 7)
    # Selected: {2, 3, 4, 5, 6, 7}
    # Phase 3: Remaining quota (up to 10 lines)
    # Total selected should be 10 lines, prioritized by severity and recency.

    prioritized = preprocessor._prioritize_logs(logs)

    assert len(prioritized) == 10
    assert "Line 3: ERROR Critical failure here" in prioritized
    assert "Line 6: PANIC System collapse" in prioritized
    # Context window checks
    assert "Line 2: INFO Process 2" in prioritized
    assert "Line 4: INFO Cleanup 1" in prioritized
    assert "Line 5: INFO Idle" in prioritized
    assert "Line 7: INFO Cleanup 2" in prioritized

def test_logsage_noise_filtering():
    preprocessor = LogSagePreprocessor()
    assert preprocessor.is_noise("heartbeat") is True
    assert preprocessor.is_noise("Normal operation") is False

def test_logsage_severity_scoring():
    preprocessor = LogSagePreprocessor()
    assert preprocessor.get_severity_score("CRITICAL error") == 100
    assert preprocessor.get_severity_score("ERROR happened") == 80
    assert preprocessor.get_severity_score("Just info") == 10

def test_logsage_deduplication():
    preprocessor = LogSagePreprocessor()
    logs = ["A", "A", "B", "C", "C", "C", "A"]
    assert preprocessor.deduplicate(logs) == ["A", "B", "C", "A"]

def test_logsage_process_with_truncation():
    preprocessor = LogSagePreprocessor(max_output_lines=2)
    raw_logs = "INFO 1\nERROR 2\nPANIC 3\nINFO 4"
    processed = preprocessor.process(raw_logs)
    # Filtered: ["INFO 1", "ERROR 2", "PANIC 3", "INFO 4"]
    # Anchors: "ERROR 2", "PANIC 3"
    # Max output lines is 2, so should only contain the anchors.
    assert len(processed) == 2
    assert "ERROR 2" in processed
    assert "PANIC 3" in processed

def test_logsage_empty_logs():
    preprocessor = LogSagePreprocessor()
    assert preprocessor.process("") == []
    assert preprocessor._prioritize_logs([]) == []
