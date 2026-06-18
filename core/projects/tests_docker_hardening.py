import pytest
from unittest.mock import MagicMock, patch
from projects.docker_client import HardenedContainerCollection, HardenedDockerClient

def test_hardened_container_collection_blocks_privileged():
    mock_collection = MagicMock()
    hardened = HardenedContainerCollection(mock_collection)

    with pytest.raises(PermissionError) as excinfo:
        hardened.run("nginx", privileged=True)
    assert "Security Policy Violation" in str(excinfo.value)
    assert "privileged" in str(excinfo.value)

    with pytest.raises(PermissionError):
        hardened.create("nginx", privileged=True)

def test_hardened_container_collection_blocks_cap_add():
    mock_collection = MagicMock()
    hardened = HardenedContainerCollection(mock_collection)

    with pytest.raises(PermissionError) as excinfo:
        hardened.run("nginx", cap_add=["SYS_ADMIN"])
    assert "cap_add" in str(excinfo.value)

def test_hardened_container_collection_blocks_recursive():
    mock_collection = MagicMock()
    hardened = HardenedContainerCollection(mock_collection)

    # Test nested dictionary check
    with pytest.raises(PermissionError) as excinfo:
        hardened.run("nginx", storage_opt={"devices": ["/dev/sda"]})
    assert "devices" in str(excinfo.value)

def test_hardened_container_collection_allows_safe_params():
    mock_collection = MagicMock()
    hardened = HardenedContainerCollection(mock_collection)

    hardened.run("nginx", detach=True, ports={'80/tcp': 8080})
    mock_collection.run.assert_called_once_with("nginx", detach=True, ports={'80/tcp': 8080})

def test_hardened_docker_client_restricts_api_access():
    mock_client = MagicMock()
    hardened = HardenedDockerClient(mock_client)

    with pytest.raises(PermissionError) as excinfo:
        _ = hardened.api
    assert "Direct access to low-level Docker API 'api' is restricted" in str(excinfo.value)

def test_hardened_docker_client_proxies_other_attributes():
    mock_client = MagicMock()
    mock_client.version.return_value = "1.41"
    hardened = HardenedDockerClient(mock_client)

    # We need to bypass the __getattribute__ check for _client itself if we want to call it directly,
    # but the implementation of HardenedDockerClient handles proxying via __getattr__.
    # The error happens because `hardened.version()` calls `getattr(self, 'version')`
    # which triggers `__getattribute__('version')`, which then tries to return `super().__getattribute__(name)`
    # if it's not in the restricted list.
    assert hardened.version() == "1.41"

def test_hardened_container_collection_proxies_attributes():
    mock_collection = MagicMock()
    mock_collection.list.return_value = []
    hardened = HardenedContainerCollection(mock_collection)

    assert hardened.list() == []
