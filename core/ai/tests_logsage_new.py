import pytest
from core.ai.logsage import LogSagePreprocessor

def test_is_noise():
    preprocessor = LogSagePreprocessor()
    assert preprocessor.is_noise("heartbeat") is True
    assert preprocessor.is_noise("GET /health") is True
    assert preprocessor.is_noise("Something important") is False

def test_get_severity_score():
    preprocessor = LogSagePreprocessor()
    assert preprocessor.get_severity_score("CRITICAL failure") == 100
    assert preprocessor.get_severity_score("ERROR happened") == 80
    assert preprocessor.get_severity_score("Just some info") == 10

def test_deduplicate():
    preprocessor = LogSagePreprocessor()
    logs = ["error", "error", "info", "error"]
    assert preprocessor.deduplicate(logs) == ["error", "info", "error"]

def test_process_empty():
    preprocessor = LogSagePreprocessor()
    assert preprocessor.process("") == []

def test_process_basic():
    preprocessor = LogSagePreprocessor(max_output_lines=5)
    raw_logs = "info 1\ninfo 2\nERROR 1\ninfo 3\ninfo 4\ninfo 5"
    processed = preprocessor.process(raw_logs)
    assert "ERROR 1" in processed
    assert len(processed) <= 5

def test_process_prioritization():
    # max_output_lines = 3, context_window = 1
    preprocessor = LogSagePreprocessor(max_output_lines=3, context_window=1)
    # The ERROR line is at index 5 (6th line)
    raw_logs = "line 0\nline 1\nline 2\nline 3\nline 4\nCRITICAL ERROR\nline 6\nline 7"
    processed = preprocessor.process(raw_logs)

    # Anchors first, then context
    # CRITICAL ERROR should be there
    assert "CRITICAL ERROR" in processed
    # Context should be there: line 4 and line 6
    assert "line 4" in processed
    assert "line 6" in processed
    assert len(processed) == 3

def test_process_noise_filtering():
    preprocessor = LogSagePreprocessor()
    raw_logs = "important error\nheartbeat\nstatus 200"
    processed = preprocessor.process(raw_logs)
    assert processed == ["important error"]

def test_process_deduplication():
    preprocessor = LogSagePreprocessor()
    raw_logs = "error\nerror\nerror"
    processed = preprocessor.process(raw_logs)
    assert processed == ["error"]

def test_process_under_limit():
    preprocessor = LogSagePreprocessor(max_output_lines=10)
    raw_logs = "line 1\nline 2"
    assert preprocessor.process(raw_logs) == ["line 1", "line 2"]
