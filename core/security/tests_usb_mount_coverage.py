import pytest
from unittest.mock import patch, MagicMock
from security.usb_mount import USBMountManager
import os

def test_mount_volume_non_absolute_mount_point():
    result = USBMountManager.mount_volume("/dev/sdb1", "mnt/usb/stick")
    assert not result

@patch("os.path.normpath")
def test_mount_volume_normalization_error(mock_normpath):
    mock_normpath.side_effect = Exception("Normalization error")
    result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
    assert not result

def test_mount_volume_invalid_device_path():
    result = USBMountManager.mount_volume("/etc/passwd", "/mnt/usb/stick")
    assert not result

def test_mount_volume_invalid_mount_point():
    result = USBMountManager.mount_volume("/dev/sdb1", "/tmp/stick")
    assert not result

def test_mount_volume_mount_directly_on_base():
    result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb")
    assert not result

@patch("os.path.commonpath")
def test_mount_volume_commonpath_value_error(mock_commonpath):
    # Success first for line 45, failure second for line 53
    mock_commonpath.side_effect = ["/dev", ValueError("Invalid paths")]
    result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
    assert not result

@patch("security.usb_mount.USBGuardManager.is_installed")
def test_mount_volume_usbguard_not_installed(mock_is_installed):
    mock_is_installed.return_value = False
    result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
    assert not result

@patch("security.usb_mount.USBGuardManager.is_installed")
@patch("os.path.exists")
@patch("os.makedirs")
def test_mount_volume_os_makedirs_error(mock_makedirs, mock_exists, mock_is_installed):
    mock_is_installed.return_value = True
    mock_exists.return_value = False
    mock_makedirs.side_effect = OSError("Failed to create directory")
    result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
    assert not result

@patch("security.usb_mount.os.path.exists")
@patch("security.usb_mount.os.makedirs")
@patch("security.usb_mount.Path.is_block_device")
@patch("security.usb_mount.USBGuardManager.list_devices")
@patch("security.usb_mount.USBGuardManager.is_service_active")
@patch("security.usb_mount.USBGuardManager.is_installed")
@patch("security.usb_mount.subprocess.run")
def test_mount_volume_security_options_passed(mock_run, mock_installed, mock_active, mock_list, mock_block, mock_makedirs, mock_exists):
    mock_installed.return_value = True
    mock_active.return_value = True
    mock_list.return_value = "allow /dev/sdb1"
    mock_block.return_value = True
    mock_exists.return_value = True
    mock_run.return_value = MagicMock(returncode=0)

    result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
    assert result

    assert mock_run.called
    args, kwargs = mock_run.call_args
    command = args[0]
    assert "-o" in command
    assert "noexec,nosuid,nodev" in command
