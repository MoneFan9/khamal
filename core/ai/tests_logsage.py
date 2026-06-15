import pytest
from core.ai.logsage import LogSagePreprocessor

@pytest.fixture
def preprocessor():
    return LogSagePreprocessor(max_output_lines=5, context_window=1)

def test_is_noise(preprocessor):
    assert preprocessor.is_noise("GET /health HTTP/1.1 200")
    assert preprocessor.is_noise("heartbeat: ok")
    assert not preprocessor.is_noise("ERROR: Database connection failed")

def test_get_severity_score(preprocessor):
    assert preprocessor.get_severity_score("CRITICAL failure") == 100
    assert preprocessor.get_severity_score("ERROR: something") == 80
    assert preprocessor.get_severity_score("INFO: just data") == 10

def test_deduplicate(preprocessor):
    logs = ["line1", "line1", "line2", "line1"]
    deduped = preprocessor.deduplicate(logs)
    assert deduped == ["line1", "line2", "line1"]

def test_process_empty(preprocessor):
    assert preprocessor.process("") == []
    assert preprocessor.process(None) == []

def test_process_small(preprocessor):
    logs = "INFO: log1\nINFO: log2"
    res = preprocessor.process(logs)
    assert res == ["INFO: log1", "INFO: log2"]

def test_prioritization_logic(preprocessor):
    # We set max_output_lines=3, context_window=1
    preprocessor.max_output_lines = 3
    logs = [
        "INFO: start",      # 0
        "INFO: step 1",     # 1
        "CRITICAL: crash",  # 2 - ANCHOR
        "INFO: step 2",     # 3
        "INFO: end"         # 4
    ]
    # Should pick index 2 (anchor), then 1 and 3 (context), and stop (max 3)
    res = preprocessor.process("\n".join(logs))
    assert len(res) == 3
    assert "CRITICAL: crash" in res
    assert "INFO: step 1" in res
    assert "INFO: step 2" in res
    # Verify it stays chronological
    assert res == ["INFO: step 1", "CRITICAL: crash", "INFO: step 2"]

def test_noise_filtering_in_process(preprocessor):
    logs = "INFO: normal\nGET /metrics 200\nERROR: crash"
    res = preprocessor.process(logs)
    assert "INFO: normal" in res
    assert "ERROR: crash" in res
    assert "GET /metrics 200" not in res
