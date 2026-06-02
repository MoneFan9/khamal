import pytest
from core.ai.rag import RCAPromptBuilder

def test_rca_prompt_builder_truncation():
    """
    Tests that logs are correctly truncated if they exceed max_log_chars.
    """
    max_chars = 100
    builder = RCAPromptBuilder(max_log_chars=max_chars)

    long_logs = ["A" * 60, "B" * 60] # Total 121 chars with newline
    prompt = builder.build_prompt(long_logs)

    assert "... [truncated — showing last portion] ..." in prompt.user
    # The last part should be the end of the logs
    assert prompt.user.endswith("B" * 60 + "\n```\n\n---\n**Response Format**: Use clear Markdown headers.\n")

def test_rca_prompt_builder_repr():
    """
    Tests the __repr__ method of RCAPromptBuilder.
    """
    builder = RCAPromptBuilder(max_log_chars=500, enable_tools=True)
    representation = repr(builder)

    assert "RCAPromptBuilder" in representation
    assert "max_log_chars=500" in representation
    assert "enable_tools=True" in representation
    assert "custom_system_prompt=False" in representation

def test_rca_prompt_builder_custom_system_prompt_repr():
    """
    Tests the __repr__ method with a custom system prompt.
    """
    builder = RCAPromptBuilder(system_prompt="Custom Prompt")
    representation = repr(builder)

    assert "custom_system_prompt=True" in representation

def test_rca_prompt_builder_empty_logs():
    """
    Tests that build_prompt raises ValueError if logs list is empty.
    """
    builder = RCAPromptBuilder()
    with pytest.raises(ValueError, match="logs must be a non-empty list of strings"):
        builder.build_prompt([])

def test_rca_prompt_builder_none_logs():
    """
    Tests that build_prompt raises ValueError if logs is None.
    """
    builder = RCAPromptBuilder()
    with pytest.raises(ValueError, match="logs must be a non-empty list of strings"):
        builder.build_prompt(None)
