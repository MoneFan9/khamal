import pytest
from unittest.mock import patch, MagicMock
import subprocess
import os
from core.security.usb_mount import USBMountManager

@patch("core.security.usb_mount.Path.is_block_device")
@patch("core.security.usb_mount.USBGuardManager.is_installed")
@patch("core.security.usb_mount.USBGuardManager.is_service_active")
@patch("core.security.usb_mount.USBGuardManager.list_devices")
def test_mount_volume_list_devices_none(mock_list, mock_active, mock_installed, mock_block):
    mock_block.return_value = True
    mock_installed.return_value = True
    mock_active.return_value = True
    mock_list.return_value = None

    assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test") is False

@patch("core.security.usb_mount.Path.is_block_device")
@patch("core.security.usb_mount.USBGuardManager.is_installed")
@patch("core.security.usb_mount.USBGuardManager.is_service_active")
@patch("core.security.usb_mount.USBGuardManager.list_devices")
@patch("os.path.exists")
@patch("os.makedirs")
def test_mount_volume_makedirs_oserror(mock_makedirs, mock_exists, mock_list, mock_active, mock_installed, mock_block):
    mock_block.return_value = True
    mock_installed.return_value = True
    mock_active.return_value = True
    mock_list.return_value = "allow /dev/sdb1"
    mock_exists.return_value = False
    mock_makedirs.side_effect = OSError("Disk full")

    assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test") is False

@patch("core.security.usb_mount.Path.is_block_device")
@patch("core.security.usb_mount.USBGuardManager.is_installed")
@patch("core.security.usb_mount.USBGuardManager.is_service_active")
@patch("core.security.usb_mount.USBGuardManager.list_devices")
@patch("os.path.exists")
@patch("subprocess.run")
def test_mount_volume_subprocess_error(mock_run, mock_exists, mock_list, mock_active, mock_installed, mock_block):
    mock_block.return_value = True
    mock_installed.return_value = True
    mock_active.return_value = True
    mock_list.return_value = "allow /dev/sdb1"
    mock_exists.return_value = True
    mock_run.side_effect = subprocess.CalledProcessError(1, "mount", stderr="Mount failed")

    assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test") is False

def test_unmount_volume_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "umount", stderr="Busy")
        assert USBMountManager.unmount_volume("/mnt/usb/test") is False
