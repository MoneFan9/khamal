import pytest
from unittest.mock import patch, MagicMock
from core.ai.client import OllamaClient
import requests

@pytest.fixture
def ollama_client(settings):
    settings.OLLAMA_URL = "http://test:11434"
    settings.OLLAMA_KEEP_ALIVE = "1m"
    return OllamaClient()

@patch("requests.post")
def test_generate(mock_post, ollama_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "hi"}
    mock_post.return_value = mock_response

    res = ollama_client.generate("m1", "p1")
    assert res["response"] == "hi"
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["model"] == "m1"
    assert kwargs["json"]["keep_alive"] == "1m"

@patch("requests.post")
def test_generate_streaming(mock_post, ollama_client):
    mock_response = MagicMock()
    mock_response.iter_lines.return_value = [b"line1", b"line2"]
    mock_post.return_value = mock_response

    res = ollama_client.generate("m1", "p1", stream=True)
    assert list(res) == [b"line1", b"line2"]

@patch("requests.post")
def test_chat(mock_post, ollama_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": {"content": "hello"}}
    mock_post.return_value = mock_response

    messages = [{"role": "user", "content": "hello"}]
    res = ollama_client.chat("m1", messages)
    assert res["message"]["content"] == "hello"

@patch("requests.get")
def test_list_models(mock_get, ollama_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"models": []}
    mock_get.return_value = mock_response
    res = ollama_client.list_models()
    assert res["models"] == []

@patch("requests.post")
def test_pull_model(mock_post, ollama_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "success"}
    mock_post.return_value = mock_response
    res = ollama_client.pull_model("m1")
    assert res["status"] == "success"

@patch("requests.post")
def test_show_model(mock_post, ollama_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"modelfile": "..."}
    mock_post.return_value = mock_response
    res = ollama_client.show_model("m1")
    assert res["modelfile"] == "..."

@patch("requests.post")
def test_unload_model(mock_post, ollama_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "unloaded"}
    mock_post.return_value = mock_response
    res = ollama_client.unload_model("m1")
    assert res["status"] == "unloaded"
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["keep_alive"] == 0

@patch("requests.post")
def test_session_context_manager(mock_post, ollama_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    mock_post.return_value = mock_response

    with ollama_client.session("m1") as session:
        assert session == ollama_client

    # Verify unload_model was called
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["model"] == "m1"
    assert kwargs["json"]["keep_alive"] == 0

@patch("requests.post")
def test_generate_full(mock_post, ollama_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    mock_post.return_value = mock_response

    ollama_client.generate(
        "m1", "p1",
        system="sys", template="tpl", context=[1,2], options={"num_ctx": 4096}
    )
    args, kwargs = mock_post.call_args
    payload = kwargs["json"]
    assert payload["system"] == "sys"
    assert payload["template"] == "tpl"
    assert payload["context"] == [1,2]
    assert payload["options"] == {"num_ctx": 4096}

@patch("requests.post")
def test_chat_full(mock_post, ollama_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    mock_post.return_value = mock_response

    ollama_client.chat(
        "m1", [{"role": "user", "content": "h"}],
        tools=[{"type": "function"}], options={"temp": 0.0}
    )
    args, kwargs = mock_post.call_args
    payload = kwargs["json"]
    assert payload["tools"] == [{"type": "function"}]
    assert payload["options"] == {"temp": 0.0}
