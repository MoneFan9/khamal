import pytest
import os
from unittest.mock import patch, MagicMock
from django.conf import settings
from projects.serializers import LocalSourceSerializer
from security.usb_mount import USBMountManager

def test_local_source_serializer_valid_path():
    """Test LocalSourceSerializer with a valid path inside BASE_DIR."""
    valid_path = os.path.realpath(os.path.join(str(settings.BASE_DIR), "projects", "my-project"))
    serializer = LocalSourceSerializer(data={
        'host_path': valid_path,
        'container_path': '/app'
    })
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data['host_path'] == valid_path

def test_local_source_serializer_invalid_path_traversal():
    """Test LocalSourceSerializer with a path traversal attempt."""
    invalid_path = os.path.join(str(settings.BASE_DIR), "..", "..", "etc", "passwd")
    serializer = LocalSourceSerializer(data={
        'host_path': invalid_path,
        'container_path': '/app'
    })
    assert not serializer.is_valid()
    assert 'host_path' in serializer.errors

def test_local_source_serializer_non_absolute_path():
    """Test LocalSourceSerializer with a non-absolute path."""
    serializer = LocalSourceSerializer(data={
        'host_path': 'relative/path',
        'container_path': '/app'
    })
    assert not serializer.is_valid()
    assert 'host_path' in serializer.errors

def test_local_source_serializer_outside_base_dir():
    """Test LocalSourceSerializer with a path outside allowed BASE_DIR."""
    serializer = LocalSourceSerializer(data={
        'host_path': '/etc/passwd',
        'container_path': '/app'
    })
    assert not serializer.is_valid()
    assert 'host_path' in serializer.errors

@patch("security.usb_mount.Path.is_block_device")
@patch("security.usb_mount.USBGuardManager.list_devices")
@patch("security.usb_mount.USBGuardManager.is_service_active")
@patch("security.usb_mount.USBGuardManager.is_installed")
@patch("os.path.exists")
@patch("os.makedirs")
@patch("subprocess.run")
def test_usb_mount_valid(mock_run, mock_makedirs, mock_exists, mock_usbguard, mock_active, mock_list, mock_block):
    """Test USBMountManager with valid parameters and verify flags."""
    mock_usbguard.return_value = True
    mock_active.return_value = True
    mock_list.return_value = "allow /dev/sdb1"
    mock_block.return_value = True
    mock_exists.return_value = False
    mock_run.return_value = MagicMock(returncode=0)

    result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/my-stick")
    assert result

    # Verify that the correct security flags are passed
    args, kwargs = mock_run.call_args
    command = args[0]
    assert "-o" in command
    assert "noexec,nosuid,nodev" in command
    assert "/dev/sdb1" in command
    assert "/mnt/usb/my-stick" in command

@patch("security.usb_mount.USBGuardManager.is_installed")
def test_usb_mount_invalid_device(mock_usbguard):
    """Test USBMountManager with an invalid device path (outside /dev)."""
    mock_usbguard.return_value = True
    result = USBMountManager.mount_volume("/etc/passwd", "/mnt/usb/my-stick")
    assert not result

@patch("security.usb_mount.USBGuardManager.is_installed")
def test_usb_mount_invalid_mount_point(mock_usbguard):
    """Test USBMountManager with an invalid mount point (outside /mnt/usb)."""
    mock_usbguard.return_value = True
    result = USBMountManager.mount_volume("/dev/sdb1", "/home/user/my-stick")
    assert not result

@patch("security.usb_mount.USBGuardManager.is_installed")
def test_usb_mount_prefix_bypass(mock_usbguard):
    """Test USBMountManager with prefix bypass attempt (e.g., /mnt/usb-escape)."""
    mock_usbguard.return_value = True
    result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb-escape")
    assert not result

@patch("security.usb_mount.USBGuardManager.is_installed")
def test_usb_mount_direct_base(mock_usbguard):
    """Test USBMountManager with direct mount on the base directory."""
    mock_usbguard.return_value = True
    result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb")
    assert not result

@patch("security.usb_mount.USBGuardManager.is_installed")
def test_usb_mount_no_usbguard(mock_usbguard):
    """Test USBMountManager when USBGuard is not installed."""
    mock_usbguard.return_value = False
    result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/my-stick")
    assert not result

@patch("security.usb_mount.USBGuardManager.is_service_active")
@patch("security.usb_mount.USBGuardManager.is_installed")
def test_usb_mount_inactive_service(mock_installed, mock_active):
    """Test USBMountManager when USBGuard service is inactive."""
    mock_installed.return_value = True
    mock_active.return_value = False
    result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/my-stick")
    assert not result

@patch("projects.docker_client.docker.DockerClient")
def test_docker_privileged_blocked(mock_docker):
    """Test that the hardened Docker client blocks privileged=True."""
    from projects.docker_client import get_docker_client
    client = get_docker_client()

    with pytest.raises(PermissionError) as cm:
        client.containers.run("alpine", privileged=True)
    assert "privileged" in str(cm.value)

@patch("projects.docker_client.docker.DockerClient")
def test_docker_cap_add_blocked(mock_docker):
    """Test that the hardened Docker client blocks cap_add."""
    from projects.docker_client import get_docker_client
    client = get_docker_client()

    with pytest.raises(PermissionError) as cm:
        client.containers.create("alpine", cap_add=["NET_ADMIN"])
    assert "cap_add" in str(cm.value)

@patch("projects.docker_client.docker.DockerClient")
def test_docker_forbidden_modes_blocked(mock_docker):
    """Test that forbidden modes are blocked."""
    from projects.docker_client import get_docker_client
    client = get_docker_client()

    forbidden = ['network_mode', 'ipc_mode', 'uts_mode', 'sysctls']
    for param in forbidden:
        with pytest.raises(PermissionError) as cm:
            kwargs = {param: "host" if param != 'sysctls' else {"net.ipv4.ip_forward": 1}}
            client.containers.run("alpine", **kwargs)
        assert param in str(cm.value)
