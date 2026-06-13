from django.test import TestCase
from unittest.mock import patch, MagicMock
from security.usb_mount import USBMountManager
from security.usb_guard import USBGuardManager
import subprocess
import os

class USBMountCoverageTests(TestCase):

    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_list_devices_none(self, mock_installed, mock_active, mock_list):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = None

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.Path.is_block_device")
    def test_mount_volume_service_inactive(self, mock_block, mock_installed, mock_active):
        mock_installed.return_value = True
        mock_block.return_value = True
        mock_active.return_value = False

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_usb_guard_generate_policy_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard")
        self.assertIsNone(USBGuardManager.generate_policy())

    @patch("subprocess.Popen")
    def test_usb_guard_apply_policy_failure(self, mock_popen):
        mock_process = MagicMock()
        mock_process.communicate.return_value = (None, b"Error")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        self.assertFalse(USBGuardManager.apply_policy("allow all"))

    @patch("subprocess.run")
    def test_usb_guard_list_devices_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard")
        self.assertIsNone(USBGuardManager.list_devices())

    @patch("security.usb_mount.Path.is_block_device")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_mount_volume_makedirs_oserror(self, mock_makedirs, mock_exists, mock_installed, mock_active, mock_list, mock_block):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "allow /dev/sdb1"
        mock_block.return_value = True
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Disk full")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.Path.is_block_device")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("os.path.exists")
    @patch("subprocess.run")
    def test_mount_volume_subprocess_error(self, mock_run, mock_exists, mock_installed, mock_active, mock_list, mock_block):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "allow /dev/sdb1"
        mock_block.return_value = True
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "mount", stderr="Generic error")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)
