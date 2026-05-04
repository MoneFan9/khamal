from django.test import TestCase
from unittest.mock import patch
from security.usb_mount import USBMountManager
import os

class USBMountExtendedTests(TestCase):

    @patch("security.usb_mount.os.path.normpath")
    def test_mount_volume_normalization_error(self, mock_normpath):
        mock_normpath.side_effect = Exception("Mocked error")
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    def test_mount_volume_non_absolute_mount_point(self):
        result = USBMountManager.mount_volume("/dev/sdb1", "mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.os.path.commonpath")
    def test_mount_volume_commonpath_value_error(self, mock_commonpath):
        # First call to commonpath (validation of device_path) returns /dev
        # Second call to commonpath (validation of mount_point) raises ValueError
        mock_commonpath.side_effect = ["/dev", ValueError("Mocked error")]

        with self.assertLogs("security.usb_mount", level="ERROR") as cm:
            result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
            self.assertFalse(result)
            self.assertIn("Invalid paths for commonpath", cm.output[0])

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.os.path.exists")
    @patch("security.usb_mount.os.makedirs")
    def test_mount_volume_makedirs_oserror(self, mock_makedirs, mock_exists, mock_usbguard):
        mock_usbguard.return_value = True
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Mocked error")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)
