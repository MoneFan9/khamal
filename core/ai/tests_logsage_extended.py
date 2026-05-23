import pytest
from ai.logsage import LogSagePreprocessor

@pytest.fixture
def preprocessor():
    return LogSagePreprocessor(max_output_lines=5, context_window=1)

def test_logsage_is_noise(preprocessor):
    assert preprocessor.is_noise("heartbeat") is True
    assert preprocessor.is_noise("Normal log line") is False
    assert preprocessor.is_noise("GET /health HTTP/1.1") is True

def test_logsage_severity_score(preprocessor):
    assert preprocessor.get_severity_score("CRITICAL error") == 100
    assert preprocessor.get_severity_score("Some INFO message") == 10
    assert preprocessor.get_severity_score("Unrecognized level") == 10

def test_logsage_deduplicate(preprocessor):
    logs = ["error1", "error1", "error2", "error2", "error2", "error1"]
    assert preprocessor.deduplicate(logs) == ["error1", "error2", "error1"]

def test_logsage_process_basic(preprocessor):
    raw_logs = """
    INFO: Starting app
    INFO: heartbeat
    ERROR: Something went wrong
    INFO: Continuing
    """
    processed = preprocessor.process(raw_logs)
    # "heartbeat" should be filtered out
    # "Starting app", "Something went wrong", "Continuing" should remain
    assert "INFO: heartbeat" not in processed
    assert "ERROR: Something went wrong" in processed

def test_logsage_prioritization_mpps(preprocessor):
    # max_output_lines = 5, context_window = 1
    raw_logs = "\n".join([
        "INFO: line 0",
        "INFO: line 1",
        "INFO: line 2",
        "CRITICAL: line 3 (anchor)",
        "INFO: line 4",
        "INFO: line 5",
        "INFO: line 6",
        "ERROR: line 7 (anchor)",
        "INFO: line 8",
        "INFO: line 9",
    ])

    processed = preprocessor.process(raw_logs)

    # Anchors should be present: line 3 and line 7
    # Context window (1): line 2, line 4 (for line 3) and line 6, line 8 (for line 7)
    # Total selected might exceed 5, so it will prioritize anchors first, then context, then remaining.

    assert "CRITICAL: line 3 (anchor)" in processed
    assert "ERROR: line 7 (anchor)" in processed
    # Since max_output_lines is 5, we expect 5 lines total.
    assert len(processed) == 5

def test_logsage_empty_logs(preprocessor):
    assert preprocessor.process("") == []
    assert preprocessor.process(None) == []

def test_logsage_no_prioritization_needed(preprocessor):
    # If logs are fewer than max_output_lines, all (non-noise) should be returned
    preprocessor.max_output_lines = 10
    logs = "INFO: log1\nINFO: log2"
    assert preprocessor.process(logs) == ["INFO: log1", "INFO: log2"]
