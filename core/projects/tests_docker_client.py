import pytest
from unittest.mock import MagicMock
from core.projects.docker_client import HardenedDockerClient, HardenedContainerCollection

def test_hardened_container_collection_run_valid():
    mock_collection = MagicMock()
    hardened = HardenedContainerCollection(mock_collection)
    hardened.run(image="alpine", command="echo hello")
    mock_collection.run.assert_called_with(image="alpine", command="echo hello")

def test_hardened_container_collection_run_forbidden():
    mock_collection = MagicMock()
    hardened = HardenedContainerCollection(mock_collection)
    with pytest.raises(PermissionError, match="Security Policy Violation"):
        hardened.run(image="alpine", privileged=True)

def test_hardened_container_collection_run_recursive_forbidden():
    mock_collection = MagicMock()
    hardened = HardenedContainerCollection(mock_collection)
    with pytest.raises(PermissionError, match="Security Policy Violation"):
        hardened.run(image="alpine", host_config={"privileged": True})

def test_hardened_docker_client_restricted_access():
    mock_client = MagicMock()
    hardened = HardenedDockerClient(mock_client)
    with pytest.raises(PermissionError, match="Direct access to low-level Docker API"):
        _ = hardened.api
    with pytest.raises(PermissionError, match="Direct access to low-level Docker API"):
        _ = hardened._client

def test_hardened_docker_client_transparent_getattr():
    mock_client = MagicMock()
    mock_client.images = "mock_images"
    hardened = HardenedDockerClient(mock_client)
    assert hardened.images == "mock_images"

def test_hardened_container_collection_getattr():
    mock_collection = MagicMock()
    mock_collection.get.return_value = "container"
    hardened = HardenedContainerCollection(mock_collection)
    assert hardened.get("id") == "container"
