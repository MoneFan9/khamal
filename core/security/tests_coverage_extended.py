from django.test import TestCase
from unittest.mock import patch, MagicMock
from security.usb_guard import USBGuardManager
from security.usb_mount import USBMountManager
from pathlib import Path
import subprocess
import os

class USBGuardCoverageTests(TestCase):
    @patch("subprocess.run")
    def test_generate_policy_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard", stderr="Error")
        self.assertIsNone(USBGuardManager.generate_policy())

    @patch("subprocess.run")
    def test_list_devices_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard", stderr="Error")
        self.assertIsNone(USBGuardManager.list_devices())

    @patch("subprocess.run")
    def test_allow_device_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard")
        self.assertFalse(USBGuardManager.allow_device(1))

    @patch("subprocess.run")
    def test_block_device_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard")
        self.assertFalse(USBGuardManager.block_device(1))

    @patch("subprocess.Popen")
    def test_apply_policy_failure(self, mock_popen):
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (None, None)
        mock_popen.return_value = mock_process
        self.assertFalse(USBGuardManager.apply_policy("allow all"))

    @patch("subprocess.Popen")
    def test_apply_policy_exception(self, mock_popen):
        mock_popen.side_effect = subprocess.CalledProcessError(1, "sudo")
        self.assertFalse(USBGuardManager.apply_policy("allow all"))

    @patch("subprocess.run")
    def test_is_service_active_failure(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        self.assertFalse(USBGuardManager.is_service_active())

class USBMountCoverageTests(TestCase):
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.Path.is_block_device")
    @patch("os.path.exists")
    def test_mount_volume_usbguard_installed_but_inactive(self, mock_exists, mock_block, mock_list, mock_active, mock_installed):
        mock_installed.return_value = True
        mock_active.return_value = False
        mock_block.return_value = True
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.Path.is_block_device")
    @patch("os.path.exists")
    def test_mount_volume_list_devices_fails(self, mock_exists, mock_block, mock_list, mock_active, mock_installed):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = None
        mock_block.return_value = True
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.Path.is_block_device")
    def test_mount_volume_not_authorized(self, mock_block, mock_list, mock_active, mock_installed):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "allow /dev/other"
        mock_block.return_value = True
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_unmount_volume_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "umount", stderr="error")
        result = USBMountManager.unmount_volume("/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.Path.is_block_device")
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_mount_volume_makedirs_failure(self, mock_makedirs, mock_exists, mock_block, mock_list, mock_active, mock_installed):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "allow /dev/sdb1"
        mock_block.return_value = True
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Permission denied")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_usbguard_not_installed(self, mock_installed):
        mock_installed.return_value = False
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)
