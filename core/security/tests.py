from django.test import TestCase
from unittest.mock import patch, MagicMock
from security.usb_guard import USBGuardManager
from security.usb_mount import USBMountManager
import subprocess
import os
import stat

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
    def test_is_service_active_true(self, mock_run):
        mock_run.return_value = MagicMock(stdout="active\n", returncode=0)
        self.assertTrue(USBGuardManager.is_service_active())

    @patch("subprocess.run")
    def test_is_service_active_false(self, mock_run):
        mock_run.return_value = MagicMock(stdout="inactive\n", returncode=0)
        self.assertFalse(USBGuardManager.is_service_active())

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

    @patch("security.usb_mount.os.stat")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.os.path.exists")
    @patch("security.usb_mount.os.makedirs")
    @patch("security.usb_mount.subprocess.run")
    def test_mount_volume_success(self, mock_run, mock_makedirs, mock_exists, mock_usbguard, mock_active, mock_list, mock_stat):
        mock_usbguard.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "1: allow id 1234:5678 serial \"\" name \"\" hash \"\" parent-hash \"\" via-port \"usb1\" with-interface { 08:06:50 } with-connect-type \"\" with-devpath \"/dev/sdb1\""

        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mode = stat.S_IFBLK
        mock_stat.return_value = mock_stat_obj

        mock_exists.return_value = False
        mock_run.return_value = MagicMock(returncode=0)

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")

        self.assertTrue(result)
        mock_makedirs.assert_called_once_with("/mnt/usb/stick", exist_ok=True)
        mock_run.assert_called_with(
            ["sudo", "mount", "-o", "noexec,nosuid,nodev", "/dev/sdb1", "/mnt/usb/stick"],
            check=True, capture_output=True, text=True
        )

    @patch("security.usb_mount.os.stat")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.os.path.exists")
    @patch("security.usb_mount.subprocess.run")
    def test_mount_volume_failure(self, mock_run, mock_exists, mock_usbguard, mock_active, mock_list, mock_stat):
        mock_usbguard.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "allow /dev/sdb1"

        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mode = stat.S_IFBLK
        mock_stat.return_value = mock_stat_obj

        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "mount", stderr="Permission denied")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")

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

    def test_mount_volume_invalid_paths(self):
        # Non-absolute mount point
        self.assertFalse(USBMountManager.mount_volume("/dev/sdb1", "mnt/usb/stick"))

        # Invalid device path (outside /dev)
        self.assertFalse(USBMountManager.mount_volume("/home/user/file", "/mnt/usb/stick"))

        # Invalid mount point (outside /mnt/usb)
        self.assertFalse(USBMountManager.mount_volume("/dev/sdb1", "/home/user/mount"))

        # Mounting directly on base
        self.assertFalse(USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb"))

    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_usbguard_not_installed(self, mock_installed):
        mock_installed.return_value = False
        self.assertFalse(USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick"))

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("os.makedirs")
    @patch("os.path.exists")
    def test_mount_volume_makedirs_failure(self, mock_exists, mock_makedirs, mock_installed):
        mock_installed.return_value = True
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Permission denied")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("os.path.normpath")
    def test_mount_volume_normalization_error(self, mock_normpath):
        mock_normpath.side_effect = Exception("Normalization failed")
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("os.path.commonpath")
    def test_mount_volume_commonpath_value_error(self, mock_commonpath):
        # We need to let the first call to commonpath succeed (for /dev validation)
        # and make the second one fail (for /mnt/usb validation)
        mock_commonpath.side_effect = ["/dev", ValueError("Invalid paths")]
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)
