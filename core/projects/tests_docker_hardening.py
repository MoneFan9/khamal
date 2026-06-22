import pytest
from unittest.mock import MagicMock, patch
from projects.docker_client import get_docker_client

@patch("docker.DockerClient")
def test_hardened_client_blocks_forbidden_params(mock_docker):
    # Mock the internal client to avoid connection errors
    mock_client = MagicMock()
    mock_docker.return_value = mock_client

    client = get_docker_client()

    forbidden_scenarios = [
        {'network_mode': 'host'},
        {'ipc_mode': 'host'},
        {'uts_mode': 'host'},
        {'sysctls': {'net.ipv4.ip_forward': '1'}},
        {'privileged': True},
        {'cap_add': ['SYS_ADMIN']}
    ]

    for scenario in forbidden_scenarios:
        with pytest.raises(PermissionError) as excinfo:
            client.containers.run("alpine", **scenario)
        assert "Security Policy Violation: Use of forbidden Docker parameter" in str(excinfo.value)

@patch("docker.DockerClient")
def test_hardened_client_blocks_sensitive_mounts(mock_docker):
    mock_client = MagicMock()
    mock_docker.return_value = mock_client

    client = get_docker_client()

    sensitive_mounts = [
        {'/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'ro'}},
        {'/etc/shadow': {'bind': '/shadow', 'mode': 'ro'}},
        {'/etc/passwd': {'bind': '/passwd', 'mode': 'ro'}},
        {'/root': {'bind': '/root', 'mode': 'rw'}},
        {'/etc/sudoers': {'bind': '/sudoers', 'mode': 'ro'}}
    ]

    for volumes in sensitive_mounts:
        with pytest.raises(PermissionError) as excinfo:
            client.containers.run("alpine", volumes=volumes)
        assert "Security Policy Violation: Mounting sensitive host path" in str(excinfo.value)

@patch("docker.DockerClient")
def test_hardened_client_blocks_path_normalization_bypass(mock_docker):
    mock_client = MagicMock()
    mock_docker.return_value = mock_client
    client = get_docker_client()

    bypass_paths = [
        {'/var/run/./docker.sock': {'bind': '/docker.sock', 'mode': 'ro'}},
        {'/etc/../etc/shadow': {'bind': '/shadow', 'mode': 'ro'}},
        {'/var/run/docker.sock/': {'bind': '/docker.sock', 'mode': 'ro'}}
    ]

    for volumes in bypass_paths:
        with pytest.raises(PermissionError) as excinfo:
            client.containers.run("alpine", volumes=volumes)
        assert "Security Policy Violation: Mounting sensitive host path" in str(excinfo.value)

@patch("docker.DockerClient")
def test_hardened_client_blocks_parent_directory_mount(mock_docker):
    mock_client = MagicMock()
    mock_docker.return_value = mock_client
    client = get_docker_client()

    parent_mounts = [
        {'/etc': {'bind': '/etc_host', 'mode': 'ro'}},
        {'/var/run': {'bind': '/var_run_host', 'mode': 'ro'}}
    ]

    for volumes in parent_mounts:
        with pytest.raises(PermissionError) as excinfo:
            client.containers.run("alpine", volumes=volumes)
        assert "Security Policy Violation: Mounting sensitive host path" in str(excinfo.value)

@patch("docker.DockerClient")
def test_hardened_client_blocks_mount_objects(mock_docker):
    mock_client = MagicMock()
    mock_docker.return_value = mock_client
    client = get_docker_client()

    from docker.types import Mount
    mounts = [
        Mount(target="/docker.sock", source="/var/run/docker.sock", type="bind")
    ]

    with pytest.raises(PermissionError) as excinfo:
        client.containers.run("alpine", mounts=mounts)
    assert "Security Policy Violation: Mounting sensitive host path" in str(excinfo.value)

@patch("docker.DockerClient")
def test_hardened_client_blocks_sensitive_mounts_list_format(mock_docker):
    mock_client = MagicMock()
    mock_docker.return_value = mock_client

    client = get_docker_client()

    volumes = ['/var/run/docker.sock:/var/run/docker.sock:ro']

    with pytest.raises(PermissionError) as excinfo:
        client.containers.run("alpine", volumes=volumes)
    assert "Security Policy Violation: Mounting sensitive host path" in str(excinfo.value)

@patch("docker.DockerClient")
def test_hardened_client_restricts_direct_api_access(mock_docker):
    mock_client = MagicMock()
    mock_docker.return_value = mock_client

    client = get_docker_client()

    with pytest.raises(PermissionError) as excinfo:
        _ = client.api
    assert "Direct access to low-level Docker API 'api' is restricted" in str(excinfo.value)

    with pytest.raises(PermissionError) as excinfo:
        _ = client._client
    assert "Direct access to low-level Docker API '_client' is restricted" in str(excinfo.value)
