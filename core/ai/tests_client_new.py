import pytest
from unittest.mock import patch, MagicMock
from core.ai.client import OllamaClient
import requests

@pytest.fixture
def ollama_client():
    return OllamaClient(base_url="http://test-ollama:11434")

def test_init_defaults():
    with patch("core.ai.client.getattr") as mock_getattr:
        mock_getattr.side_effect = lambda obj, attr, default: default
        client = OllamaClient()
        assert client.base_url == "http://localhost:11434"
        assert client.keep_alive == "5m"

@patch("requests.post")
def test_generate(mock_post, ollama_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "test response"}
    mock_post.return_value = mock_response

    result = ollama_client.generate("llama3", "Hello")

    assert result == {"response": "test response"}
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "http://test-ollama:11434/api/generate"
    assert kwargs["json"]["model"] == "llama3"
    assert kwargs["json"]["prompt"] == "Hello"

@patch("requests.post")
def test_generate_stream(mock_post, ollama_client):
    mock_response = MagicMock()
    mock_response.iter_lines.return_value = [b'line1', b'line2']
    mock_post.return_value = mock_response

    result = ollama_client.generate("llama3", "Hello", stream=True)

    assert list(result) == [b'line1', b'line2']

@patch("requests.post")
def test_chat(mock_post, ollama_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": {"content": "hi"}}
    mock_post.return_value = mock_response

    messages = [{"role": "user", "content": "hi"}]
    result = ollama_client.chat("llama3", messages)

    assert result == {"message": {"content": "hi"}}
    mock_post.assert_called_once()

@patch("requests.get")
def test_list_models(mock_get, ollama_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"models": []}
    mock_get.return_value = mock_response

    result = ollama_client.list_models()
    assert result == {"models": []}
    mock_get.assert_called_once_with("http://test-ollama:11434/api/tags")

@patch("requests.post")
def test_pull_model(mock_post, ollama_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "success"}
    mock_post.return_value = mock_response

    result = ollama_client.pull_model("llama3")
    assert result == {"status": "success"}
    mock_post.assert_called_once()

@patch("requests.post")
def test_show_model(mock_post, ollama_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"details": "..."}
    mock_post.return_value = mock_response

    result = ollama_client.show_model("llama3")
    assert result == {"details": "..."}
    mock_post.assert_called_once()

@patch("requests.post")
def test_unload_model(mock_post, ollama_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "unloaded"}
    mock_post.return_value = mock_response

    result = ollama_client.unload_model("llama3")
    assert result == {"status": "unloaded"}
    kwargs = mock_post.call_args[1]
    assert kwargs["json"]["keep_alive"] == 0

def test_session_context_manager(ollama_client):
    with patch.object(OllamaClient, "unload_model") as mock_unload:
        with ollama_client.session("llama3") as session:
            assert session == ollama_client
        mock_unload.assert_called_once_with("llama3")

def test_session_context_manager_exception(ollama_client):
    with patch.object(OllamaClient, "unload_model") as mock_unload:
        try:
            with ollama_client.session("llama3"):
                raise ValueError("Oops")
        except ValueError:
            pass
        mock_unload.assert_called_once_with("llama3")
