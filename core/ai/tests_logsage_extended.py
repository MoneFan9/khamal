import pytest
from core.ai.logsage import LogSagePreprocessor

def test_logsage_preprocessor_init():
    lp = LogSagePreprocessor(max_output_lines=50, context_window=5)
    assert lp.max_output_lines == 50
    assert lp.context_window == 5

def test_is_noise():
    lp = LogSagePreprocessor()
    assert lp.is_noise("heartbeat: ok") is True
    assert lp.is_noise("GET /health HTTP/1.1") is True
    assert lp.is_noise("status 200 OK") is True
    assert lp.is_noise("Something important happened") is False

def test_get_severity_score():
    lp = LogSagePreprocessor()
    assert lp.get_severity_score("CRITICAL error") == 100
    assert lp.get_severity_score("EXCEPTION: something") == 90
    assert lp.get_severity_score("ERROR: failed") == 80
    assert lp.get_severity_score("WARNING: careful") == 40
    assert lp.get_severity_score("INFO: ok") == 10
    assert lp.get_severity_score("DEBUG: detail") == 0
    assert lp.get_severity_score("random text") == 10

def test_deduplicate():
    lp = LogSagePreprocessor()
    logs = ["line1", "line1", "line2", "line2", "line2", "line3"]
    assert lp.deduplicate(logs) == ["line1", "line2", "line3"]

def test_process_empty():
    lp = LogSagePreprocessor()
    assert lp.process("") == []
    assert lp.process(None) == []

def test_process_simple():
    lp = LogSagePreprocessor()
    raw = "INFO: log1\nINFO: log2"
    assert lp.process(raw) == ["INFO: log1", "INFO: log2"]

def test_process_with_noise_and_dedup():
    lp = LogSagePreprocessor()
    raw = "INFO: log1\nheartbeat\nheartbeat\nINFO: log1\nINFO: log2"
    # log1, heartbeat(noise), heartbeat(noise), log1, log2
    # -> log1, log1, log2 (filtered noise)
    # -> log1, log2 (deduplicated)
    assert lp.process(raw) == ["INFO: log1", "INFO: log2"]

def test_prioritization_anchors():
    # max 2 lines, but we have 3 critical ones.
    # It should take the last ones due to recency weighting if they have same severity.
    lp = LogSagePreprocessor(max_output_lines=2, context_window=0)
    raw = "CRITICAL: 1\nCRITICAL: 2\nCRITICAL: 3"
    processed = lp.process(raw)
    assert len(processed) == 2
    assert "CRITICAL: 2" in processed
    assert "CRITICAL: 3" in processed

def test_prioritization_context_window():
    lp = LogSagePreprocessor(max_output_lines=5, context_window=1)
    raw = "\n".join([
        "INFO: 1",
        "INFO: 2",
        "ERROR: anchor",
        "INFO: 4",
        "INFO: 5",
        "INFO: 6"
    ])
    processed = lp.process(raw)
    # anchor is index 2. context is 1, 2, 3.
    # Plus remaining quota.
    assert "INFO: 2" in processed
    assert "ERROR: anchor" in processed
    assert "INFO: 4" in processed

def test_fill_remaining_quota():
    lp = LogSagePreprocessor(max_output_lines=3, context_window=0)
    raw = "ERROR: 1\nINFO: 2\nINFO: 3\nINFO: 4"
    processed = lp.process(raw)
    # anchor: ERROR 1
    # quota: INFO 4, INFO 3 (due to recency)
    assert processed == ["ERROR: 1", "INFO: 3", "INFO: 4"]
