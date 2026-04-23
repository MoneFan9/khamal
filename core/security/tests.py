from django.test import TestCase
from unittest.mock import patch, MagicMock
from security.usb_guard import USBGuardManager
from security.usb_mount import USBMountManager
import subprocess
import os

class USBGuardTests(TestCase):

    @patch("subprocess.run")
    def test_is_installed_true(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(USBGuardManager.is_installed())

    @patch("subprocess.run")
    def test_is_installed_false(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        self.assertFalse(USBGuardManager.is_installed())

    @patch("subprocess.run")
    def test_generate_policy_success(self, mock_run):
        mock_run.return_value = MagicMock(stdout="allow id 1234:5678", returncode=0)
        policy = USBGuardManager.generate_policy()
        self.assertEqual(policy, "allow id 1234:5678")

    @patch("subprocess.Popen")
    @patch("subprocess.run")
    def test_apply_policy_success(self, mock_run, mock_popen):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (None, None)
        mock_popen.return_value = mock_process

        mock_run.return_value = MagicMock(returncode=0)

        result = USBGuardManager.apply_policy("allow all")
        self.assertTrue(result)
        mock_popen.assert_called_once()
        mock_run.assert_called_with(["sudo", "systemctl", "restart", "usbguard"], check=True)

    @patch("subprocess.run")
    def test_list_devices(self, mock_run):
        mock_run.return_value = MagicMock(stdout="1: allow id 1d6b:0002", returncode=0)
        devices = USBGuardManager.list_devices()
        self.assertEqual(devices, "1: allow id 1d6b:0002")

    @patch("subprocess.run")
    def test_allow_device(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = USBGuardManager.allow_device(1)
        self.assertTrue(result)
        mock_run.assert_called_with(["sudo", "usbguard", "allow-device", "1"], check=True)

    @patch("subprocess.run")
    def test_block_device(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = USBGuardManager.block_device(1)
        self.assertTrue(result)
        mock_run.assert_called_with(["sudo", "usbguard", "block-device", "1"], check=True)

class USBMountTests(TestCase):

    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("subprocess.run")
    def test_mount_volume_success(self, mock_run, mock_makedirs, mock_exists):
        mock_exists.return_value = False
        mock_run.return_value = MagicMock(returncode=0)

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb")

        self.assertTrue(result)
        mock_makedirs.assert_called_once_with("/mnt/usb", exist_ok=True)
        mock_run.assert_called_with(
            ["sudo", "mount", "-o", "noexec,nosuid,nodev", "/dev/sdb1", "/mnt/usb"],
            check=True, capture_output=True, text=True
        )

    @patch("os.path.exists")
    @patch("subprocess.run")
    def test_mount_volume_failure(self, mock_run, mock_exists):
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "mount", stderr="Permission denied")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb")

        self.assertFalse(result)

    @patch("subprocess.run")
    def test_unmount_volume_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        result = USBMountManager.unmount_volume("/mnt/usb")

        self.assertTrue(result)
        mock_run.assert_called_with(
            ["sudo", "umount", "/mnt/usb"],
            check=True, capture_output=True, text=True
        )

    @patch("subprocess.run")
    def test_unmount_volume_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "umount", stderr="Target is busy")

        result = USBMountManager.unmount_volume("/mnt/usb")

        self.assertFalse(result)
