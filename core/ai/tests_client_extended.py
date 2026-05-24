import pytest
import requests_mock
from core.ai.client import OllamaClient

@pytest.fixture
def ollama_client():
    return OllamaClient(base_url="http://test-ollama:11434")

def test_ollama_client_init():
    client = OllamaClient(base_url="http://custom:11434")
    assert client.base_url == "http://custom:11434"
    assert client.api_url == "http://custom:11434/api"

def test_generate_success(ollama_client):
    with requests_mock.Mocker() as m:
        m.post("http://test-ollama:11434/api/generate", json={"response": "Hello"}, status_code=200)

        response = ollama_client.generate(model="llama3", prompt="Hi")
        assert response["response"] == "Hello"
        assert m.called
        assert m.request_history[0].json()["model"] == "llama3"
        assert m.request_history[0].json()["prompt"] == "Hi"

def test_generate_with_options(ollama_client):
    with requests_mock.Mocker() as m:
        m.post("http://test-ollama:11434/api/generate", json={"response": "Hello"}, status_code=200)

        ollama_client.generate(
            model="llama3",
            prompt="Hi",
            system="You are a bot",
            template="Custom template",
            context=[1, 2, 3],
            options={"temperature": 0.5},
            keep_alive="10m"
        )

        sent_json = m.request_history[0].json()
        assert sent_json["system"] == "You are a bot"
        assert sent_json["template"] == "Custom template"
        assert sent_json["context"] == [1, 2, 3]
        assert sent_json["options"] == {"temperature": 0.5}
        assert sent_json["keep_alive"] == "10m"

def test_chat_success(ollama_client):
    messages = [{"role": "user", "content": "Hello"}]
    with requests_mock.Mocker() as m:
        m.post("http://test-ollama:11434/api/chat", json={"message": {"content": "Hi"}}, status_code=200)

        response = ollama_client.chat(model="llama3", messages=messages)
        assert response["message"]["content"] == "Hi"
        assert m.request_history[0].json()["messages"] == messages

def test_list_models(ollama_client):
    with requests_mock.Mocker() as m:
        m.get("http://test-ollama:11434/api/tags", json={"models": []}, status_code=200)
        response = ollama_client.list_models()
        assert response == {"models": []}

def test_pull_model(ollama_client):
    with requests_mock.Mocker() as m:
        m.post("http://test-ollama:11434/api/pull", json={"status": "success"}, status_code=200)
        response = ollama_client.pull_model("llama3")
        assert response == {"status": "success"}

def test_show_model(ollama_client):
    with requests_mock.Mocker() as m:
        m.post("http://test-ollama:11434/api/show", json={"details": "info"}, status_code=200)
        response = ollama_client.show_model("llama3")
        assert response == {"details": "info"}

def test_unload_model(ollama_client):
    with requests_mock.Mocker() as m:
        m.post("http://test-ollama:11434/api/generate", json={"status": "unloaded"}, status_code=200)
        response = ollama_client.unload_model("llama3")
        assert response == {"status": "unloaded"}
        assert m.request_history[0].json()["keep_alive"] == 0

def test_session_context_manager(ollama_client):
    with requests_mock.Mocker() as m:
        m.post("http://test-ollama:11434/api/generate", json={"status": "unloaded"}, status_code=200)
        with ollama_client.session("llama3") as session:
            assert session == ollama_client

        assert m.called
        assert m.request_history[0].json()["model"] == "llama3"
        assert m.request_history[0].json()["keep_alive"] == 0
