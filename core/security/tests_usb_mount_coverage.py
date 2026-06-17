from django.test import TestCase
from unittest.mock import patch, MagicMock
from security.usb_mount import USBMountManager
import subprocess
import os

class USBMountCoverageTests(TestCase):

    @patch("security.usb_mount.Path.is_block_device")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    def test_mount_volume_usbguard_service_inactive(self, mock_active, mock_installed, mock_block):
        mock_installed.return_value = True
        mock_active.return_value = False
        mock_block.return_value = True

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.Path.is_block_device")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    def test_mount_volume_usbguard_list_devices_failure(self, mock_list, mock_active, mock_installed, mock_block):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_block.return_value = True
        mock_list.return_value = None

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.Path.is_block_device")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    def test_mount_volume_parent_authorization_success(self, mock_list, mock_active, mock_installed, mock_block):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_block.return_value = True
        # Parent device /dev/sdb is authorized
        mock_list.return_value = "1: allow id 1234:5678 ... with-devpath \"/dev/sdb\""

        with patch("os.path.exists", return_value=True), \
             patch("subprocess.run", return_value=MagicMock(returncode=0)):
            result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
            self.assertTrue(result)

    def test_validate_paths_normalization_error(self):
        with patch("os.path.normpath", side_effect=Exception("Error")):
            result, _, _ = USBMountManager._validate_paths("/dev/sdb1", "/mnt/usb/stick")
            self.assertFalse(result)

    def test_validate_paths_commonpath_value_error(self):
        # First call for /dev succeeds, second for /mnt/usb fails
        with patch("os.path.commonpath", side_effect=["/dev", ValueError("Error")]):
            result, _, _ = USBMountManager._validate_paths("/dev/sdb1", "/mnt/usb/stick")
            self.assertFalse(result)
