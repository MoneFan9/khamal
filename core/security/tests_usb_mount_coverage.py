from django.test import TestCase
from unittest.mock import patch, MagicMock
from security.usb_mount import USBMountManager
import os

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
        # Line 45 uses commonpath once, but we want to trigger the try/except at line 53
        # So we make it succeed the first time and fail the second time.
        mock_commonpath.side_effect = ["/dev", ValueError("Invalid paths")]
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_usbguard_not_installed(self, mock_is_installed):
        mock_is_installed.return_value = False
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_mount_volume_os_makedirs_error(self, mock_makedirs, mock_exists, mock_is_installed):
        mock_is_installed.return_value = True
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Failed to create directory")
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.Path.is_block_device")
    def test_mount_volume_not_block_device(self, mock_is_block):
        mock_is_block.return_value = False
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)
        mock_is_block.assert_called_once()
