import pytest
import requests
from unittest.mock import MagicMock
from .client import OllamaClient

@pytest.fixture
def client():
    return OllamaClient(base_url="http://ollama-test:11434")

def test_generate_error(client, mocker):
    mock_post = mocker.patch("requests.post")
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Error")
    mock_post.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError):
        client.generate(model="llama3", prompt="Hi")

def test_chat_error(client, mocker):
    mock_post = mocker.patch("requests.post")
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Not Found")
    mock_post.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError):
        client.chat(model="llama3", messages=[])

def test_list_models_error(client, mocker):
    mock_get = mocker.patch("requests.get")
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Service Unavailable")
    mock_get.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError):
        client.list_models()

def test_pull_model_error(client, mocker):
    mock_post = mocker.patch("requests.post")
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Bad Request")
    mock_post.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError):
        client.pull_model(name="invalid")

def test_show_model_error(client, mocker):
    mock_post = mocker.patch("requests.post")
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Not Found")
    mock_post.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError):
        client.show_model(name="missing")

def test_unload_model_error(client, mocker):
    mock_post = mocker.patch("requests.post")
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Error")
    mock_post.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError):
        client.unload_model(model="llama3")
