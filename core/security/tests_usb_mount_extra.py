import pytest
from unittest.mock import patch, MagicMock
from core.security.usb_mount import USBMountManager
import subprocess
import os

@pytest.fixture
def mock_usbguard():
    with patch('core.security.usb_mount.USBGuardManager') as mock:
        mock.is_installed.return_value = True
        mock.is_service_active.return_value = True
        mock.list_devices.return_value = "allow device /dev/sdb1"
        yield mock

def test_mount_volume_not_block_device(mock_usbguard):
    with patch('core.security.usb_mount.os.path.exists', return_value=True), \
         patch('core.security.usb_mount.Path.is_block_device', return_value=False):

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test")
        assert result is False

def test_mount_volume_makedirs_failure(mock_usbguard):
    with patch('core.security.usb_mount.os.path.exists', return_value=False), \
         patch('core.security.usb_mount.os.makedirs', side_effect=OSError("Permission denied")):

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test")
        assert result is False

def test_mount_volume_usbguard_list_failure(mock_usbguard):
    mock_usbguard.list_devices.return_value = None
    result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test")
    assert result is False

def test_validate_paths_not_absolute():
    is_valid, _, _ = USBMountManager._validate_paths("/dev/sdb1", "mnt/usb/test")
    assert is_valid is False

def test_validate_paths_invalid_base():
    is_valid, _, _ = USBMountManager._validate_paths("/dev/sdb1", "/tmp/test")
    assert is_valid is False

def test_validate_paths_direct_base():
    is_valid, _, _ = USBMountManager._validate_paths("/dev/sdb1", "/mnt/usb")
    assert is_valid is False

def test_unmount_volume_failure():
    with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'umount', stderr='busy')):
        result = USBMountManager.unmount_volume("/mnt/usb/test")
        assert result is False

def test_mount_volume_unauthorized(mock_usbguard):
    mock_usbguard.list_devices.return_value = "allow device /dev/sda1"
    result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test")
    assert result is False
