from django.test import TestCase
from unittest.mock import patch, MagicMock
from .usb_mount import USBMountManager
import subprocess
import os

class USBMountCoverageTests(TestCase):
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    def test_mount_volume_usbguard_list_devices_none(self, mock_list, mock_active, mock_installed):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = None
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("os.path.commonpath")
    def test_mount_volume_commonpath_value_error_v3(self, mock_commonpath):
        # First call for /dev succeeds, second for /mnt/usb raises ValueError
        mock_commonpath.side_effect = ["/dev", ValueError("Invalid paths")]
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_mount_volume_makedirs_exception(self, mock_makedirs, mock_exists, mock_list, mock_active, mock_installed):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "allow /dev/sdb1"
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Disk full")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("os.path.exists")
    @patch("subprocess.run")
    def test_mount_volume_mount_failure(self, mock_run, mock_exists, mock_list, mock_active, mock_installed):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "allow /dev/sdb1"
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "mount", stderr="mount: /mnt/usb/stick: permission denied")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)
