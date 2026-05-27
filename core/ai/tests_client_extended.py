import pytest
import requests
import requests_mock
from django.conf import settings
from ai.client import OllamaClient

@pytest.fixture
def client():
    return OllamaClient(base_url="http://test-ollama:11434")

def test_init_default(settings):
    settings.OLLAMA_URL = "http://config-ollama:11434"
    settings.OLLAMA_KEEP_ALIVE = "10m"
    client = OllamaClient()
    assert client.base_url == "http://config-ollama:11434"
    assert client.keep_alive == "10m"
    assert client.api_url == "http://config-ollama:11434/api"

def test_generate_success(client, requests_mock):
    requests_mock.post(
        "http://test-ollama:11434/api/generate",
        json={"response": "Hello world", "done": True}
    )

    response = client.generate(model="llama3", prompt="Hi")
    assert response["response"] == "Hello world"
    assert requests_mock.called
    assert requests_mock.request_history[0].json()["prompt"] == "Hi"

def test_generate_with_options(client, requests_mock):
    requests_mock.post("http://test-ollama:11434/api/generate", json={})

    client.generate(
        model="llama3",
        prompt="Hi",
        system="Be helpful",
        template="{{ .Prompt }}",
        context=[1, 2, 3],
        options={"temperature": 0.5},
        keep_alive="1h"
    )

    payload = requests_mock.request_history[0].json()
    assert payload["system"] == "Be helpful"
    assert payload["template"] == "{{ .Prompt }}"
    assert payload["context"] == [1, 2, 3]
    assert payload["options"] == {"temperature": 0.5}
    assert payload["keep_alive"] == "1h"

def test_generate_stream(client, requests_mock):
    requests_mock.post("http://test-ollama:11434/api/generate", text="line1\nline2\n")

    response = client.generate(model="llama3", prompt="Hi", stream=True)
    lines = list(response)
    assert len(lines) == 2
    assert lines[0] == b"line1"

def test_chat_success(client, requests_mock):
    requests_mock.post(
        "http://test-ollama:11434/api/chat",
        json={"message": {"role": "assistant", "content": "How can I help?"}}
    )

    messages = [{"role": "user", "content": "Hi"}]
    response = client.chat(model="llama3", messages=messages)
    assert response["message"]["content"] == "How can I help?"

    payload = requests_mock.request_history[0].json()
    assert payload["messages"] == messages

def test_chat_with_tools(client, requests_mock):
    requests_mock.post("http://test-ollama:11434/api/chat", json={})

    tools = [{"type": "function", "function": {"name": "test"}}]
    client.chat(model="llama3", messages=[], tools=tools, options={"num_predict": 10})

    payload = requests_mock.request_history[0].json()
    assert payload["tools"] == tools
    assert payload["options"] == {"num_predict": 10}

def test_list_models(client, requests_mock):
    requests_mock.get(
        "http://test-ollama:11434/api/tags",
        json={"models": [{"name": "llama3"}]}
    )

    response = client.list_models()
    assert response["models"][0]["name"] == "llama3"

def test_pull_model(client, requests_mock):
    requests_mock.post(
        "http://test-ollama:11434/api/pull",
        json={"status": "success"}
    )

    response = client.pull_model(name="llama3")
    assert response["status"] == "success"
    assert requests_mock.request_history[0].json()["name"] == "llama3"

def test_show_model(client, requests_mock):
    requests_mock.post(
        "http://test-ollama:11434/api/show",
        json={"modelfile": "FROM llama3"}
    )

    response = client.show_model(name="llama3")
    assert response["modelfile"] == "FROM llama3"
    assert requests_mock.request_history[0].json()["name"] == "llama3"

def test_unload_model(client, requests_mock):
    requests_mock.post(
        "http://test-ollama:11434/api/generate",
        json={"done": True}
    )

    response = client.unload_model(model="llama3")
    payload = requests_mock.request_history[0].json()
    assert payload["model"] == "llama3"
    assert payload["keep_alive"] == 0

def test_session_context_manager(client, requests_mock):
    # Mock both chat/generate and unload
    requests_mock.post("http://test-ollama:11434/api/chat", json={"done": True})
    requests_mock.post("http://test-ollama:11434/api/generate", json={"done": True})

    with client.session(model="llama3") as s:
        s.chat(model="llama3", messages=[])

    # Check that unload was called
    unload_request = next(r for r in requests_mock.request_history if "/api/generate" in r.url)
    assert unload_request.json()["keep_alive"] == 0

def test_session_context_manager_exception(client, requests_mock):
    requests_mock.post("http://test-ollama:11434/api/generate", json={"done": True})

    try:
        with client.session(model="llama3") as s:
            raise ValueError("Test error")
    except ValueError:
        pass

    # Unload should still be called
    assert requests_mock.called
    assert any("/api/generate" in r.url for r in requests_mock.request_history)

def test_api_error(client, requests_mock):
    requests_mock.post("http://test-ollama:11434/api/generate", status_code=500)

    with pytest.raises(requests.exceptions.HTTPError):
        client.generate(model="llama3", prompt="Hi")
