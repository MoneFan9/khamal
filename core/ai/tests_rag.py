import pytest
from .rag import RCAPromptBuilder, RCAPrompt

@pytest.fixture
def builder():
    return RCAPromptBuilder()

def test_build_prompt_basic(builder):
    logs = ["ERROR: Connection refused", "INFO: Retrying..."]
    prompt_obj = builder.build_prompt(logs)

    assert isinstance(prompt_obj, RCAPrompt)
    assert "### Environment Context" in prompt_obj.user
    assert "ERROR: Connection refused" in prompt_obj.user
    assert "**Project Name**: Unknown" in prompt_obj.user
    assert prompt_obj.system == builder.SYSTEM_PROMPT

def test_to_ollama_messages(builder):
    logs = ["ERROR: Fail"]
    prompt_obj = builder.build_prompt(logs)
    messages = prompt_obj.to_ollama_messages()

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[0]["content"] == prompt_obj.system
    assert messages[1]["content"] == prompt_obj.user

def test_build_prompt_with_context(builder):
    logs = ["ERROR: Syntax error"]
    context = {
        "project_name": "MyCoolApp",
        "language": "Django/Python",
        "environment": "Development",
        "ignored_key": "ShouldNotBeHere"
    }
    prompt_obj = builder.build_prompt(logs, project_context=context)

    assert "**Project Name**: MyCoolApp" in prompt_obj.user
    assert "**Primary Language/Framework**: Django/Python" in prompt_obj.user
    assert "**Deployment Environment**: Development" in prompt_obj.user
    assert "ignored_key" not in prompt_obj.user

def test_empty_logs_raises_value_error(builder):
    with pytest.raises(ValueError):
        builder.build_prompt([])

def test_invalid_logs_raises_value_error(builder):
    with pytest.raises(ValueError):
        builder.build_prompt([None])

def test_truncation():
    short_builder = RCAPromptBuilder(max_log_chars=10)
    logs = ["This is a long log line"]
    prompt_obj = short_builder.build_prompt(logs)

    assert "[truncated" in prompt_obj.user
    # It should keep the end of the log (before the closing markers)
    assert "g log line\n```" in prompt_obj.user

def test_custom_template():
    custom_template = "PROJECT: {project_name} LOGS: {logs}"
    builder = RCAPromptBuilder(rca_template=custom_template)
    logs = ["log1"]
    prompt_obj = builder.build_prompt(logs, project_context={"project_name": "Test"})

    assert prompt_obj.user == "PROJECT: Test LOGS: log1"

def test_repr(builder):
    assert "RCAPromptBuilder" in repr(builder)
    assert "max_log_chars=12000" in repr(builder)

def test_get_system_prompt(builder):
    assert builder.get_system_prompt() == builder.SYSTEM_PROMPT
