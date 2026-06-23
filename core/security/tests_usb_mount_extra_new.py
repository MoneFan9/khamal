import pytest
import subprocess
from unittest.mock import patch, MagicMock
from core.security.usb_mount import USBMountManager

@patch("core.security.usb_mount.Path.is_block_device")
@patch("core.security.usb_mount.USBGuardManager.is_installed")
@patch("core.security.usb_mount.USBGuardManager.is_service_active")
@patch("core.security.usb_mount.USBGuardManager.list_devices")
def test_mount_volume_not_block_device(mock_list, mock_active, mock_installed, mock_is_block):
    mock_is_block.return_value = False

    result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test")
    assert result is False

@patch("core.security.usb_mount.Path.is_block_device")
@patch("core.security.usb_mount.USBGuardManager.is_installed")
@patch("core.security.usb_mount.USBGuardManager.is_service_active")
@patch("core.security.usb_mount.USBGuardManager.list_devices")
@patch("subprocess.run")
def test_mount_volume_subprocess_failure(mock_run, mock_list, mock_active, mock_installed, mock_is_block):
    mock_is_block.return_value = True
    mock_installed.return_value = True
    mock_active.return_value = True
    mock_list.return_value = "allow id 1234:5678 serial \"1234\" name \"USB\" hash \"...\" parent-hash \"...\" with-interface {08:*:*} with-connect-type \"hotplug\" /dev/sdb1"

    mock_run.side_effect = subprocess.CalledProcessError(1, "mount", stderr="Permission denied")

    with patch("os.makedirs"):
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test")
    assert result is False

def test_unmount_volume_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "umount", stderr="Device busy")
        result = USBMountManager.unmount_volume("/mnt/usb/test")
        assert result is False
