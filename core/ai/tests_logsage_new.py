import pytest
from ai.logsage import LogSagePreprocessor

@pytest.fixture
def preprocessor():
    return LogSagePreprocessor(max_output_lines=10, context_window=1)

def test_is_noise(preprocessor):
    assert preprocessor.is_noise("heartbeat detected") is True
    assert preprocessor.is_noise("health check ok") is True
    assert preprocessor.is_noise("GET /health") is True
    assert preprocessor.is_noise("ERROR: database connection failed") is False

def test_get_severity_score(preprocessor):
    assert preprocessor.get_severity_score("CRITICAL error") == 100
    assert preprocessor.get_severity_score("EXCEPTION occurred") == 90
    assert preprocessor.get_severity_score("ERROR happened") == 80
    assert preprocessor.get_severity_score("WARNING: slow query") == 40
    assert preprocessor.get_severity_score("INFO message") == 10
    assert preprocessor.get_severity_score("something else") == 10

def test_deduplicate(preprocessor):
    logs = ["error 1", "error 1", "error 2", "error 2", "error 1"]
    assert preprocessor.deduplicate(logs) == ["error 1", "error 2", "error 1"]

def test_process_empty(preprocessor):
    assert preprocessor.process("") == []
    assert preprocessor.process(None) == []

def test_process_simple(preprocessor):
    raw_logs = "info 1\ninfo 2\ninfo 3"
    assert preprocessor.process(raw_logs) == ["info 1", "info 2", "info 3"]

def test_process_with_noise_and_dedup(preprocessor):
    raw_logs = "heartbeat\nerror 1\nerror 1\nhealth check\nerror 2"
    assert preprocessor.process(raw_logs) == ["error 1", "error 2"]

def test_prioritization_strategy(preprocessor):
    # Set max_output_lines to 3 and context_window to 1
    p = LogSagePreprocessor(max_output_lines=3, context_window=1)

    # We want to see:
    # 1. Anchors (score >= 80)
    # 2. Context around anchors
    # 3. Rest by priority

    logs = [
        "info 0",
        "info 1",
        "CRITICAL 2", # Anchor
        "info 3",
        "info 4",
        "ERROR 5",    # Anchor
        "info 6"
    ]
    raw_logs = "\n".join(logs)

    processed = p.process(raw_logs)

    # max_output_lines=3
    # Anchors: CRITICAL 2 (index 2), ERROR 5 (index 5)
    # Phase 1: Add anchors -> {2, 5}
    # Phase 2: Add context -> for 2: {1, 2, 3}. But limit is 3. So might add 1 and stop.
    # Result should be exactly 3 lines.

    assert len(processed) == 3
    assert "CRITICAL 2" in processed
    assert "ERROR 5" in processed

def test_recency_weight(preprocessor):
    p = LogSagePreprocessor(max_output_lines=2)
    logs = [
        "WARNING 1",
        "WARNING 2",
        "WARNING 3"
    ]
    raw_logs = "\n".join(logs)
    processed = p.process(raw_logs)

    # Later warnings should have higher score due to (i/total_logs)*10
    # WARNING 3 (index 2) score = 40 + 2/3*10 = 46.6
    # WARNING 2 (index 1) score = 40 + 1/3*10 = 43.3
    # WARNING 1 (index 0) score = 40 + 0 = 40

    assert processed == ["WARNING 2", "WARNING 3"]
