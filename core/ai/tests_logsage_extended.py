import pytest
from .logsage import LogSagePreprocessor

@pytest.fixture
def preprocessor():
    return LogSagePreprocessor(max_output_lines=3, context_window=1)

def test_process_no_logs(preprocessor):
    assert preprocessor.process(None) == []
    assert preprocessor.process("") == []

def test_deduplicate_empty(preprocessor):
    assert preprocessor.deduplicate([]) == []

def test_is_noise_cases(preprocessor):
    assert preprocessor.is_noise("heartbeat log") is True
    assert preprocessor.is_noise("GET /health status 200") is True
    assert preprocessor.is_noise("Normal app log") is False

def test_prioritize_logs_empty(preprocessor):
    assert preprocessor._prioritize_logs([]) == []

def test_mpps_full_cycle(preprocessor):
    logs = """
    LINE 1
    LINE 2
    PANIC: system down
    LINE 4
    LINE 5
    ERROR: another error
    LINE 7
    """
    processed = preprocessor.process(logs)
    assert len(processed) == 3
    assert any("PANIC: system down" in line for line in processed)

def test_get_severity_score_default(preprocessor):
    assert preprocessor.get_severity_score("Just some log") == 10
