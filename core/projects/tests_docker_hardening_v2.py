import pytest
from unittest.mock import MagicMock
from core.projects.docker_client import HardenedDockerClient, HardenedContainerCollection

def test_hardened_container_collection_forbidden_params():
    mock_collection = MagicMock()
    hardened = HardenedContainerCollection(mock_collection)

    # Test 'privileged'
    with pytest.raises(PermissionError, match="Use of forbidden Docker parameter 'privileged'"):
        hardened.run(image="alpine", privileged=True)

    # Test 'cap_add'
    with pytest.raises(PermissionError, match="Use of forbidden Docker parameter 'cap_add'"):
        hardened.create(image="alpine", cap_add=["SYS_ADMIN"])

    # Test recursive check
    with pytest.raises(PermissionError, match="Use of forbidden Docker parameter 'security_opt'"):
        hardened.run(image="alpine", host_config={'security_opt': ['no-new-privileges']})

def test_hardened_container_collection_allowed_params():
    mock_collection = MagicMock()
    hardened = HardenedContainerCollection(mock_collection)

    hardened.run(image="alpine", command="echo hello")
    mock_collection.run.assert_called_once_with(image="alpine", command="echo hello")

def test_hardened_docker_client_restricted_access():
    mock_client = MagicMock()
    hardened = HardenedDockerClient(mock_client)

    with pytest.raises(PermissionError, match="Direct access to low-level Docker API 'api' is restricted"):
        _ = hardened.api

    with pytest.raises(PermissionError, match="Direct access to low-level Docker API '_client' is restricted"):
        _ = hardened._client

def test_hardened_docker_client_getattr():
    mock_client = MagicMock()
    mock_client.version.return_value = {"Version": "20.10.7"}
    hardened = HardenedDockerClient(mock_client)

    assert hardened.version() == {"Version": "20.10.7"}

def test_hardened_container_collection_getattr():
    mock_collection = MagicMock()
    mock_collection.list.return_value = []
    hardened = HardenedContainerCollection(mock_collection)

    assert hardened.list() == []
