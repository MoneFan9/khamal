import pytest
from unittest.mock import MagicMock
from core.projects.docker_client import HardenedDockerClient, HardenedContainerCollection

def test_hardened_container_collection_blocks_forbidden_params():
    mock_collection = MagicMock()
    hardened = HardenedContainerCollection(mock_collection)

    # Test 'privileged'
    with pytest.raises(PermissionError, match="Use of forbidden Docker parameter 'privileged'"):
        hardened.run("image", privileged=True)

    # Test 'cap_add'
    with pytest.raises(PermissionError, match="Use of forbidden Docker parameter 'cap_add'"):
        hardened.create("image", cap_add=["SYS_ADMIN"])

    # Test nested params
    with pytest.raises(PermissionError, match="Use of forbidden Docker parameter 'devices'"):
        hardened.run("image", environment={"FOO": "BAR"}, devices=["/dev/sda:/dev/sda"])

def test_hardened_container_collection_allows_safe_params():
    mock_collection = MagicMock()
    hardened = HardenedContainerCollection(mock_collection)

    hardened.run("image", name="test-container", ports={'80/tcp': 8080})
    mock_collection.run.assert_called_once_with("image", name="test-container", ports={'80/tcp': 8080})

def test_hardened_docker_client_restricts_api_access():
    mock_client = MagicMock()
    hardened = HardenedDockerClient(mock_client)

    with pytest.raises(PermissionError, match="Direct access to low-level Docker API 'api' is restricted."):
        _ = hardened.api

    with pytest.raises(PermissionError, match="Direct access to low-level Docker API '_client' is restricted."):
        _ = hardened._client

def test_hardened_docker_client_delegates_allowed_calls():
    mock_client = MagicMock()
    mock_client.version.return_value = {"Version": "1.2.3"}
    hardened = HardenedDockerClient(mock_client)

    assert hardened.version() == {"Version": "1.2.3"}
    mock_client.version.assert_called_once()
