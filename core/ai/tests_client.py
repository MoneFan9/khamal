import pytest
import requests
import requests_mock
from django.conf import settings
from core.ai.client import OllamaClient

@pytest.fixture
def ollama_client():
    return OllamaClient(base_url="http://ollama:11434")

def test_ollama_generate(ollama_client):
    with requests_mock.Mocker() as m:
        m.post("http://ollama:11434/api/generate", json={"response": "Hello"})
        res = ollama_client.generate(model="llama3", prompt="Hi")
        assert res["response"] == "Hello"
        assert m.called
        assert m.request_history[0].json()["prompt"] == "Hi"

def test_ollama_chat(ollama_client):
    with requests_mock.Mocker() as m:
        m.post("http://ollama:11434/api/chat", json={"message": {"role": "assistant", "content": "Howdy"}})
        messages = [{"role": "user", "content": "Howdy"}]
        res = ollama_client.chat(model="llama3", messages=messages)
        assert res["message"]["content"] == "Howdy"

def test_ollama_list_models(ollama_client):
    with requests_mock.Mocker() as m:
        m.get("http://ollama:11434/api/tags", json={"models": []})
        res = ollama_client.list_models()
        assert res["models"] == []

def test_ollama_pull_model(ollama_client):
    with requests_mock.Mocker() as m:
        m.post("http://ollama:11434/api/pull", json={"status": "success"})
        res = ollama_client.pull_model("llama3")
        assert res["status"] == "success"

def test_ollama_show_model(ollama_client):
    with requests_mock.Mocker() as m:
        m.post("http://ollama:11434/api/show", json={"details": {}})
        res = ollama_client.show_model("llama3")
        assert res["details"] == {}

def test_ollama_unload_model(ollama_client):
    with requests_mock.Mocker() as m:
        m.post("http://ollama:11434/api/generate", json={"status": "unloaded"})
        res = ollama_client.unload_model("llama3")
        assert res["status"] == "unloaded"
        assert m.request_history[0].json()["keep_alive"] == 0

def test_ollama_session_context_manager(ollama_client):
    with requests_mock.Mocker() as m:
        m.post("http://ollama:11434/api/generate", json={"status": "ok"})
        with ollama_client.session("llama3") as session:
            assert session == ollama_client
        # Verify unload was called after session
        assert m.called
        assert any(r.json().get("keep_alive") == 0 for r in m.request_history)
