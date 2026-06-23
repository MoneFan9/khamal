import pytest
from unittest.mock import MagicMock
from core.projects.docker_client import HardenedDockerClient, HardenedContainerCollection

def test_hardened_client_blocks_api_access():
    mock_client = MagicMock()
    hardened = HardenedDockerClient(mock_client)

    with pytest.raises(PermissionError) as excinfo:
        _ = hardened.api
    assert "Direct access to low-level Docker API 'api' is restricted" in str(excinfo.value)

    with pytest.raises(PermissionError) as excinfo:
        _ = hardened._client
    assert "Direct access to low-level Docker API '_client' is restricted" in str(excinfo.value)

def test_hardened_container_collection_blocks_privileged():
    mock_collection = MagicMock()
    hardened_collection = HardenedContainerCollection(mock_collection)

    with pytest.raises(PermissionError) as excinfo:
        hardened_collection.run("ubuntu", privileged=True)
    assert "Security Policy Violation: Use of forbidden Docker parameter 'privileged'" in str(excinfo.value)

def test_hardened_container_collection_blocks_cap_add():
    mock_collection = MagicMock()
    hardened_collection = HardenedContainerCollection(mock_collection)

    with pytest.raises(PermissionError) as excinfo:
        hardened_collection.create("ubuntu", cap_add=["SYS_ADMIN"])
    assert "Security Policy Violation: Use of forbidden Docker parameter 'cap_add'" in str(excinfo.value)

def test_hardened_container_collection_allows_safe_params():
    mock_collection = MagicMock()
    hardened_collection = HardenedContainerCollection(mock_collection)

    hardened_collection.run("ubuntu", detach=True, environment={"FOO": "BAR"})
    mock_collection.run.assert_called_once_with("ubuntu", detach=True, environment={"FOO": "BAR"})

def test_hardened_container_collection_blocks_nested_forbidden_params():
    mock_collection = MagicMock()
    hardened_collection = HardenedContainerCollection(mock_collection)

    # Even if hidden in a dict (though run/create usually take them as kwargs)
    with pytest.raises(PermissionError):
        hardened_collection.run("ubuntu", storage_opt={"privileged": True})
