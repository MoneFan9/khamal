import pytest
from ai.logsage import LogSagePreprocessor

@pytest.fixture
def preprocessor():
    return LogSagePreprocessor(max_output_lines=10, context_window=1)

def test_is_noise(preprocessor):
    assert preprocessor.is_noise("heartbeat: ok")
    assert preprocessor.is_noise("GET /health HTTP/1.1")
    assert preprocessor.is_noise("status 200")
    assert not preprocessor.is_noise("CRITICAL: database connection failed")
    assert not preprocessor.is_noise("Something important happened")

def test_get_severity_score(preprocessor):
    assert preprocessor.get_severity_score("CRITICAL: disk full") == 100
    assert preprocessor.get_severity_score("FATAL: core dumped") == 100
    assert preprocessor.get_severity_score("EXCEPTION: null pointer") == 90
    assert preprocessor.get_severity_score("ERROR: file not found") == 80
    assert preprocessor.get_severity_score("WARNING: high latency") == 40
    assert preprocessor.get_severity_score("INFO: started server") == 10
    assert preprocessor.get_severity_score("DEBUG: variable x=5") == 0
    assert preprocessor.get_severity_score("No level here") == 10

def test_deduplicate(preprocessor):
    logs = [
        "line 1",
        "line 2",
        "line 2",
        "line 3",
        "line 1",
    ]
    expected = [
        "line 1",
        "line 2",
        "line 3",
        "line 1",
    ]
    assert preprocessor.deduplicate(logs) == expected

def test_process_empty(preprocessor):
    assert preprocessor.process("") == []
    assert preprocessor.process(None) == []

def test_process_under_limit(preprocessor):
    raw_logs = "line 1\nline 2\nline 3"
    result = preprocessor.process(raw_logs)
    assert result == ["line 1", "line 2", "line 3"]

def test_process_noise_filtering(preprocessor):
    raw_logs = "line 1\nheartbeat\nline 2\nGET /health\nline 3"
    result = preprocessor.process(raw_logs)
    assert result == ["line 1", "line 2", "line 3"]

def test_mpps_prioritization(preprocessor):
    # Set limit to 5 lines, context window 1
    p = LogSagePreprocessor(max_output_lines=5, context_window=1)

    logs = [
        "info 1",    # 0
        "info 2",    # 1
        "CRITICAL",  # 2 - Anchor 1
        "info 3",    # 3
        "info 4",    # 4
        "ERROR",     # 5 - Anchor 2
        "info 5",    # 6
        "info 6",    # 7
        "info 7",    # 8
        "info 8",    # 9
    ]
    raw_logs = "\n".join(logs)

    result = p.process(raw_logs)

    # Anchors: 2 (100), 5 (80)
    # Context for 2: 1, 2, 3
    # Context for 5: 4, 5, 6
    # Total selected by phases 1 & 2: {1, 2, 3, 4, 5, 6} (6 lines)
    # But max_output_lines is 5.

    # Phase 1 adds anchors 2 and 5. (count=2)
    # Phase 2 adds context around 2: 1 and 3. (count=4)
    # Then it tries to add context around 5: 4. (count=5). It stops there.

    assert len(result) == 5
    assert "CRITICAL" in result
    assert "ERROR" in result
    # It should include lines around the anchors
    assert result == ["info 2", "CRITICAL", "info 3", "info 4", "ERROR"]

def test_recency_weight(preprocessor):
    # Two identical errors, one at the beginning, one at the end.
    # The one at the end should have a slightly higher score.
    p = LogSagePreprocessor(max_output_lines=1, context_window=0)
    logs = [
        "ERROR at start",
        "INFO 1",
        "INFO 2",
        "ERROR at end",
    ]
    result = p.process("\n".join(logs))
    assert result == ["ERROR at end"]

def test_gen_deduplicate_internal(preprocessor):
    # Testing the internal generator-based deduplication indirectly
    raw_logs = "line 1\nline 1\nline 1"
    assert preprocessor.process(raw_logs) == ["line 1"]
