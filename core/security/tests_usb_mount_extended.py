from django.test import TestCase
from unittest.mock import patch, MagicMock
from security.usb_mount import USBMountManager
import os

class USBMountExtendedTests(TestCase):

    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_non_absolute_mount_point(self, mock_usbguard):
        mock_usbguard.return_value = True
        result = USBMountManager.mount_volume("/dev/sdb1", "mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.os.path.normpath")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_normalization_error(self, mock_usbguard, mock_normpath):
        mock_usbguard.return_value = True
        mock_normpath.side_effect = Exception("Normalization failed")
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_invalid_mount_point_outside_base(self, mock_usbguard):
        mock_usbguard.return_value = True
        # Try to mount outside /mnt/usb
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/other/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_cannot_mount_on_base(self, mock_usbguard):
        mock_usbguard.return_value = True
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb")
        self.assertFalse(result)

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_mount_volume_makedirs_failure(self, mock_makedirs, mock_exists, mock_usbguard):
        mock_usbguard.return_value = True
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Permission denied")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.os.path.commonpath")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_commonpath_value_error(self, mock_usbguard, mock_commonpath):
        mock_usbguard.return_value = True
        # Side effect only for the second call (mount point check)
        mock_commonpath.side_effect = ["/dev", ValueError("Invalid paths")]
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)
