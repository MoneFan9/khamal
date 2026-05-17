import pytest
from unittest.mock import MagicMock
from core.projects.docker_client import HardenedContainerCollection, HardenedDockerClient

def test_hardened_container_collection_run_forbidden():
    mock_coll = MagicMock()
    hardened = HardenedContainerCollection(mock_coll)

    # Check forbidden param at top level
    with pytest.raises(PermissionError, match="Security Policy Violation: Use of forbidden Docker parameter 'privileged'"):
        hardened.run(image="nginx", privileged=True)

    # Check forbidden param in nested dict (e.g. host_config if it were passed as a single dict)
    with pytest.raises(PermissionError, match="Security Policy Violation: Use of forbidden Docker parameter 'cap_add'"):
        hardened.create(image="nginx", environment={"FOO": "BAR"}, extra_params={"cap_add": ["SYS_ADMIN"]})

def test_hardened_container_collection_run_allowed():
    mock_coll = MagicMock()
    hardened = HardenedContainerCollection(mock_coll)

    hardened.run(image="nginx", detach=True, ports={'80/tcp': 8080})
    mock_coll.run.assert_called_once_with(image="nginx", detach=True, ports={'80/tcp': 8080})

def test_hardened_docker_client_restricted_access():
    mock_client = MagicMock()
    hardened = HardenedDockerClient(mock_client)

    with pytest.raises(PermissionError, match="Direct access to low-level Docker API 'api' is restricted"):
        _ = hardened.api

    with pytest.raises(PermissionError, match="Direct access to low-level Docker API '_client' is restricted"):
        _ = hardened._client

def test_hardened_docker_client_delegation():
    mock_client = MagicMock()
    mock_client.version.return_value = {"Version": "1.2.3"}
    hardened = HardenedDockerClient(mock_client)

    assert hardened.version() == {"Version": "1.2.3"}
    mock_client.version.assert_called_once()

def test_hardened_container_collection_getattr_delegation():
    mock_coll = MagicMock()
    mock_coll.get.return_value = "container_obj"
    hardened = HardenedContainerCollection(mock_coll)

    assert hardened.get("my_id") == "container_obj"
    mock_coll.get.assert_called_once_with("my_id")
