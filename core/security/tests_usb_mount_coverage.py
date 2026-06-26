from django.test import TestCase
from unittest.mock import patch, MagicMock
from security.usb_mount import USBMountManager
import os
import subprocess

class USBMountCoverageTests(TestCase):

    def test_mount_volume_non_absolute_mount_point(self):
        result = USBMountManager.mount_volume("/dev/sdb1", "mnt/usb/stick")
        self.assertFalse(result)

    @patch("os.path.normpath")
    def test_mount_volume_normalization_error(self, mock_normpath):
        mock_normpath.side_effect = Exception("Normalization error")
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    def test_mount_volume_invalid_device_path(self):
        result = USBMountManager.mount_volume("/etc/passwd", "/mnt/usb/stick")
        self.assertFalse(result)

    def test_mount_volume_invalid_mount_point(self):
        result = USBMountManager.mount_volume("/dev/sdb1", "/tmp/stick")
        self.assertFalse(result)

    def test_mount_volume_mount_directly_on_base(self):
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb")
        self.assertFalse(result)

    @patch("os.path.commonpath")
    def test_mount_volume_commonpath_value_error(self, mock_commonpath):
        mock_commonpath.side_effect = ["/dev", ValueError("Invalid paths")]
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.Path.is_block_device")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_usbguard_not_installed(self, mock_is_installed, mock_block):
        mock_block.return_value = True
        mock_is_installed.return_value = False
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.Path.is_block_device")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_mount_volume_os_makedirs_error(self, mock_makedirs, mock_exists, mock_is_installed, mock_active, mock_list, mock_block):
        mock_is_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "allow with-devpath \"/dev/sdb1\""
        mock_block.return_value = True
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Failed to create directory")
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.Path.is_block_device")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("os.path.exists")
    @patch("subprocess.run")
    def test_mount_volume_command_error(self, mock_run, mock_exists, mock_is_installed, mock_active, mock_list, mock_block):
        mock_is_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "allow with-devpath \"/dev/sdb1\""
        mock_block.return_value = True
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "mount", stderr="Mount failed")
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    def test_unmount_volume_success(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = USBMountManager.unmount_volume("/mnt/usb/stick")
            self.assertTrue(result)

    def test_unmount_volume_failure(self):
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "umount", stderr="Busy")
            result = USBMountManager.unmount_volume("/mnt/usb/stick")
            self.assertFalse(result)
