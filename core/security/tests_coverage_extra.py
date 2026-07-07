import pytest
import subprocess
import os
from unittest.mock import patch, MagicMock
from security.usb_guard import USBGuardManager
from security.usb_mount import USBMountManager

def test_usbguard_apply_policy_error_coverage():
    """Covers lines 50-52 in usb_guard.py (CalledProcessError in apply_policy)."""
    # Note: apply_policy uses subprocess.Popen then systemctl restart with subprocess.run
    with patch("security.usb_guard.subprocess.Popen") as mock_popen, \
         patch("security.usb_guard.subprocess.run", side_effect=subprocess.CalledProcessError(1, "systemctl")):

        mock_process = MagicMock()
        mock_process.communicate.return_value = (None, None)
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        # This should trigger the exception when restarting the service
        assert USBGuardManager.apply_policy("allow id 1234:5678") is False

def test_usb_mount_unmount_failure_coverage():
    """Covers unmount_volume failure branch in usb_mount.py."""
    with patch("security.usb_mount.subprocess.run", side_effect=subprocess.CalledProcessError(1, "umount", stderr="device busy")):
        assert USBMountManager.unmount_volume("/mnt/usb/stick") is False

def test_usb_mount_makedirs_error_coverage():
    """Covers os.makedirs error branch in usb_mount.py."""
    with patch("security.usb_mount.USBMountManager._validate_paths", return_value=(True, "/dev/sdb1", "/mnt/usb/stick")), \
         patch("security.usb_mount.Path.is_block_device", return_value=True), \
         patch("security.usb_guard.USBGuardManager.is_installed", return_value=True), \
         patch("security.usb_guard.USBGuardManager.is_service_active", return_value=True), \
         patch("security.usb_guard.USBGuardManager.list_devices", return_value="allow id 1234:5678 with-devpath /dev/sdb1"), \
         patch("security.usb_mount.os.path.exists", return_value=False), \
         patch("security.usb_mount.os.makedirs", side_effect=OSError("Permission denied")):

        assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick") is False

def test_usb_mount_list_devices_none_coverage():
    """Covers list_devices returning None branch in usb_mount.py."""
    with patch("security.usb_mount.USBMountManager._validate_paths", return_value=(True, "/dev/sdb1", "/mnt/usb/stick")), \
         patch("security.usb_mount.Path.is_block_device", return_value=True), \
         patch("security.usb_guard.USBGuardManager.is_installed", return_value=True), \
         patch("security.usb_guard.USBGuardManager.is_service_active", return_value=True), \
         patch("security.usb_guard.USBGuardManager.list_devices", return_value=None):

        assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick") is False
