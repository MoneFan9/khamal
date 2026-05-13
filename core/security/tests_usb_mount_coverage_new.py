import unittest
from unittest.mock import patch, MagicMock
import subprocess
import os
from core.security.usb_mount import USBMountManager

class TestUSBMountCoverage(unittest.TestCase):

    @patch("core.security.usb_mount.USBGuardManager.is_installed")
    @patch("core.security.usb_mount.USBGuardManager.is_service_active")
    @patch("core.security.usb_mount.USBGuardManager.list_devices")
    @patch("core.security.usb_mount.os.path.exists")
    @patch("core.security.usb_mount.os.makedirs")
    def test_mount_volume_makedirs_failure(self, mock_makedirs, mock_exists, mock_list, mock_active, mock_installed):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "allow /dev/sdb1"
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Disk full")

        # Mocking Path.is_block_device
        with patch("core.security.usb_mount.Path.is_block_device", return_value=True):
            result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
            self.assertFalse(result)

    @patch("core.security.usb_mount.USBGuardManager.is_installed")
    @patch("core.security.usb_mount.USBGuardManager.is_service_active")
    @patch("core.security.usb_mount.USBGuardManager.list_devices")
    @patch("core.security.usb_mount.os.path.exists")
    @patch("core.security.usb_mount.subprocess.run")
    def test_mount_volume_subprocess_failure(self, mock_run, mock_exists, mock_list, mock_active, mock_installed):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "allow /dev/sdb1"
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "mount", stderr="Generic error")

        with patch("core.security.usb_mount.Path.is_block_device", return_value=True):
            result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
            self.assertFalse(result)

    @patch("core.security.usb_mount.subprocess.run")
    def test_unmount_volume_subprocess_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "umount", stderr="Device busy")
        result = USBMountManager.unmount_volume("/mnt/usb/stick")
        self.assertFalse(result)

    def test_validate_paths_invalid_abs(self):
        # Already tested in existing tests but for coverage of the internal _validate_paths
        is_valid, _, _ = USBMountManager._validate_paths("/dev/sdb1", "relative/path")
        self.assertFalse(is_valid)

    @patch("core.security.usb_mount.os.path.normpath")
    def test_validate_paths_exception(self, mock_norm):
        mock_norm.side_effect = Exception("error")
        is_valid, _, _ = USBMountManager._validate_paths("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(is_valid)

    @patch("core.security.usb_mount.USBGuardManager.is_installed")
    @patch("core.security.usb_mount.USBGuardManager.is_service_active")
    @patch("core.security.usb_mount.USBGuardManager.list_devices")
    def test_mount_volume_list_devices_none(self, mock_list, mock_active, mock_installed):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = None

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)
