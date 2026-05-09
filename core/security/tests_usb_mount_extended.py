from django.test import TestCase
from unittest.mock import patch, MagicMock
from security.usb_mount import USBMountManager
import subprocess
import os

class USBMountExtendedTests(TestCase):

    @patch("security.usb_mount.logger")
    def test_mount_volume_non_absolute_mount_point(self, mock_logger):
        result = USBMountManager.mount_volume("/dev/sdb1", "mnt/usb/stick")
        self.assertFalse(result)
        mock_logger.error.assert_called_with("Mount point must be absolute: mnt/usb/stick")

    @patch("security.usb_mount.logger")
    @patch("os.path.normpath")
    def test_mount_volume_normalization_error(self, mock_normpath, mock_logger):
        mock_normpath.side_effect = Exception("Normalization failed")
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)
        mock_logger.error.assert_called_with("Path normalization error: Normalization failed")

    @patch("security.usb_mount.logger")
    def test_mount_volume_invalid_device_path(self, mock_logger):
        # device_path must be in /dev/
        result = USBMountManager.mount_volume("/etc/passwd", "/mnt/usb/stick")
        self.assertFalse(result)
        mock_logger.error.assert_called_with("Invalid device path (must be in /dev): /etc/passwd")

    @patch("security.usb_mount.logger")
    def test_mount_volume_invalid_mount_point_outside_base(self, mock_logger):
        # mount_point must be in /mnt/usb/
        result = USBMountManager.mount_volume("/dev/sdb1", "/tmp/stick")
        self.assertFalse(result)
        mock_logger.error.assert_called_with("Invalid mount point: /tmp/stick. Must be within /mnt/usb")

    @patch("security.usb_mount.logger")
    def test_mount_volume_mount_directly_on_base(self, mock_logger):
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb")
        self.assertFalse(result)
        mock_logger.error.assert_called_with("Cannot mount directly on /mnt/usb")

    @patch("security.usb_mount.logger")
    @patch("os.path.commonpath")
    def test_mount_volume_commonpath_value_error(self, mock_commonpath, mock_logger):
        # First call for /dev validation returns /dev
        # Second call for /mnt/usb validation raises ValueError
        mock_commonpath.side_effect = ["/dev", ValueError("Invalid paths")]
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)
        mock_logger.error.assert_called_with("Invalid paths for commonpath: /mnt/usb, /mnt/usb/stick")

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.logger")
    def test_mount_volume_usbguard_not_installed(self, mock_logger, mock_is_installed):
        mock_is_installed.return_value = False
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)
        mock_logger.error.assert_called_with("USBGuard is not installed. Refusing to mount for security reasons.")

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("security.usb_mount.logger")
    def test_mount_volume_makedirs_failure(self, mock_logger, mock_makedirs, mock_exists, mock_is_installed):
        mock_is_installed.return_value = True
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Permission denied")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)
        mock_logger.error.assert_called_with("Failed to create mount point /mnt/usb/stick: Permission denied")
