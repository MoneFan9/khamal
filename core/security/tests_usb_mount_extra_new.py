from django.test import TestCase
from unittest.mock import patch, MagicMock
from security.usb_mount import USBMountManager
import subprocess
import os

class USBMountExtraTests(TestCase):

    @patch("security.usb_mount.Path.is_block_device")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_usbguard_not_installed_coverage(self, mock_installed, mock_block):
        mock_installed.return_value = False
        mock_block.return_value = True
        self.assertFalse(USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick"))

    @patch("security.usb_mount.Path.is_block_device")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_list_devices_failure(self, mock_installed, mock_active, mock_list, mock_block):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_block.return_value = True
        mock_list.return_value = None

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.Path.is_block_device")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_mount_volume_makedirs_oserror(self, mock_makedirs, mock_exists, mock_installed, mock_active, mock_list, mock_block):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_block.return_value = True
        mock_list.return_value = "allow with-devpath \"/dev/sdb1\""
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Permission denied")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.Path.is_block_device")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("os.path.exists")
    @patch("subprocess.run")
    def test_mount_volume_subprocess_failure(self, mock_run, mock_exists, mock_installed, mock_active, mock_list, mock_block):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_block.return_value = True
        mock_list.return_value = "allow with-devpath \"/dev/sdb1\""
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "mount", stderr="Mount failed")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)
