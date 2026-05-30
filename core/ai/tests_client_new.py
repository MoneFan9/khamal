import pytest
import requests
import requests_mock
from django.conf import settings
from ai.client import OllamaClient

@pytest.fixture
def ollama_client():
    return OllamaClient(base_url="http://test-ollama:11434")

def test_ollama_client_init():
    client = OllamaClient()
    assert client.base_url == getattr(settings, "OLLAMA_URL", "http://localhost:11434")
    assert client.keep_alive == getattr(settings, "OLLAMA_KEEP_ALIVE", "5m")

def test_generate(ollama_client):
    with requests_mock.Mocker() as m:
        m.post("http://test-ollama:11434/api/generate", json={"response": "hello"})

        response = ollama_client.generate(model="llama3", prompt="hi")

        assert response["response"] == "hello"
        assert m.called
        assert m.request_history[0].json()["model"] == "llama3"
        assert m.request_history[0].json()["prompt"] == "hi"

def test_generate_with_options(ollama_client):
    with requests_mock.Mocker() as m:
        m.post("http://test-ollama:11434/api/generate", json={"response": "hello"})

        ollama_client.generate(
            model="llama3",
            prompt="hi",
            system="you are a bot",
            template="tmpl",
            context=[1, 2, 3],
            options={"temperature": 0},
            keep_alive="10m"
        )

        payload = m.request_history[0].json()
        assert payload["system"] == "you are a bot"
        assert payload["template"] == "tmpl"
        assert payload["context"] == [1, 2, 3]
        assert payload["options"] == {"temperature": 0}
        assert payload["keep_alive"] == "10m"

def test_chat(ollama_client):
    with requests_mock.Mocker() as m:
        m.post("http://test-ollama:11434/api/chat", json={"message": {"content": "hi"}})

        messages = [{"role": "user", "content": "hello"}]
        response = ollama_client.chat(model="llama3", messages=messages)

        assert response["message"]["content"] == "hi"
        assert m.called
        payload = m.request_history[0].json()
        assert payload["model"] == "llama3"
        assert payload["messages"] == messages

def test_list_models(ollama_client):
    with requests_mock.Mocker() as m:
        m.get("http://test-ollama:11434/api/tags", json={"models": []})

        response = ollama_client.list_models()
        assert response["models"] == []
        assert m.called

def test_pull_model(ollama_client):
    with requests_mock.Mocker() as m:
        m.post("http://test-ollama:11434/api/pull", json={"status": "success"})

        response = ollama_client.pull_model("llama3")
        assert response["status"] == "success"
        assert m.request_history[0].json()["name"] == "llama3"

def test_show_model(ollama_client):
    with requests_mock.Mocker() as m:
        m.post("http://test-ollama:11434/api/show", json={"details": "info"})

        response = ollama_client.show_model("llama3")
        assert response["details"] == "info"
        assert m.request_history[0].json()["name"] == "llama3"

def test_unload_model(ollama_client):
    with requests_mock.Mocker() as m:
        m.post("http://test-ollama:11434/api/generate", json={"status": "unloaded"})

        response = ollama_client.unload_model("llama3")
        assert response["status"] == "unloaded"
        payload = m.request_history[0].json()
        assert payload["model"] == "llama3"
        assert payload["keep_alive"] == 0

def test_session_context_manager(ollama_client):
    with requests_mock.Mocker() as m:
        m.post("http://test-ollama:11434/api/generate", json={"status": "unloaded"})

        with ollama_client.session("llama3") as client:
            assert client == ollama_client

        assert m.called
        assert m.request_history[0].json()["keep_alive"] == 0

def test_stream_generate(ollama_client):
     with requests_mock.Mocker() as m:
        m.post("http://test-ollama:11434/api/generate", text="line1\nline2")

        response = ollama_client.generate(model="llama3", prompt="hi", stream=True)
        lines = list(response)
        assert lines == [b"line1", b"line2"]
