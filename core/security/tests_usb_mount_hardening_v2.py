import pytest
import subprocess
import os
from unittest.mock import patch, MagicMock
from core.security.usb_mount import USBMountManager

@pytest.fixture
def mock_usb_guard():
    with patch("core.security.usb_mount.USBGuardManager") as mock:
        mock.is_installed.return_value = True
        mock.is_service_active.return_value = True
        mock.list_devices.return_value = "allow id 0123:4567 serial 123456 name device /dev/sdb1\n"
        yield mock

@pytest.fixture
def mock_path_is_block():
    with patch("core.security.usb_mount.Path.is_block_device") as mock:
        mock.return_value = True
        yield mock

def test_mount_volume_create_dir_failure(mock_usb_guard, mock_path_is_block):
    """Test failure when creating the mount point directory."""
    device_path = "/dev/sdb1"
    mount_point = "/mnt/usb/test"

    with patch("os.path.exists", return_value=False), \
         patch("os.makedirs", side_effect=OSError("Permission denied")):

        success = USBMountManager.mount_volume(device_path, mount_point)
        assert success is False

def test_mount_volume_subprocess_failure(mock_usb_guard, mock_path_is_block):
    """Test failure when the mount command fails."""
    device_path = "/dev/sdb1"
    mount_point = "/mnt/usb/test"

    with patch("os.path.exists", return_value=True), \
         patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "mount", stderr="mount error")):

        success = USBMountManager.mount_volume(device_path, mount_point)
        assert success is False

def test_unmount_volume_failure():
    """Test failure when the unmount command fails."""
    mount_point = "/mnt/usb/test"

    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "umount", stderr="umount error")):
        success = USBMountManager.unmount_volume(mount_point)
        assert success is False

def test_mount_volume_usbguard_not_installed():
    """Test failure when USBGuard is not installed."""
    device_path = "/dev/sdb1"
    mount_point = "/mnt/usb/test"
    with patch("core.security.usb_mount.Path.is_block_device", return_value=True), \
         patch("core.security.usb_mount.USBGuardManager") as mock_ug:
        mock_ug.is_installed.return_value = False

        success = USBMountManager.mount_volume(device_path, mount_point)
        assert success is False

def test_mount_volume_usbguard_devices_none():
    """Test failure when USBGuard fails to list devices."""
    device_path = "/dev/sdb1"
    mount_point = "/mnt/usb/test"
    with patch("core.security.usb_mount.Path.is_block_device", return_value=True), \
         patch("core.security.usb_mount.USBGuardManager") as mock_ug:
        mock_ug.is_installed.return_value = True
        mock_ug.is_service_active.return_value = True
        mock_ug.list_devices.return_value = None

        success = USBMountManager.mount_volume(device_path, mount_point)
        assert success is False
