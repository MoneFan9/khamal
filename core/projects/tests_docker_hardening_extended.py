import pytest
from unittest.mock import MagicMock
from core.projects.docker_client import HardenedContainerCollection

@pytest.fixture
def mock_collection():
    return MagicMock()

@pytest.fixture
def hardened_collection(mock_collection):
    return HardenedContainerCollection(mock_collection)

@pytest.mark.parametrize("params", [
    {'network_mode': 'host'},
    {'ipc_mode': 'host'},
    {'uts_mode': 'host'},
    {'sysctls': {'net.ipv4.ip_forward': 1}},
    {'privileged': True},
    {'cap_add': ['SYS_ADMIN']}
])
def test_run_with_forbidden_params(hardened_collection, params):
    with pytest.raises(PermissionError, match="Security Policy Violation"):
        hardened_collection.run("alpine", **params)

@pytest.mark.parametrize("params", [
    {'network_mode': 'host'},
    {'ipc_mode': 'host'},
    {'uts_mode': 'host'},
    {'sysctls': {'net.ipv4.ip_forward': 1}}
])
def test_create_with_forbidden_params(hardened_collection, params):
    with pytest.raises(PermissionError, match="Security Policy Violation"):
        hardened_collection.create("alpine", **params)

def test_run_with_allowed_params(hardened_collection, mock_collection):
    allowed_params = {
        'command': 'echo hello',
        'environment': {'FOO': 'BAR'},
        'volumes': {'/host/path': {'bind': '/container/path', 'mode': 'rw'}}
    }
    hardened_collection.run("alpine", **allowed_params)
    mock_collection.run.assert_called_with("alpine", **allowed_params)

def test_recursive_check(hardened_collection):
    nested_forbidden = {
        'mem_limit': '1g',
        'extra_stuff': {
            'network_mode': 'host'
        }
    }
    with pytest.raises(PermissionError):
        hardened_collection.run("alpine", **nested_forbidden)
