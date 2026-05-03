import unittest
from unittest.mock import patch, MagicMock
from security.usb_mount import USBMountManager
import os

class USBMountExtendedTest(unittest.TestCase):
    @patch('security.usb_mount.logger')
    def test_mount_volume_non_absolute_mount_point(self, mock_logger):
        result = USBMountManager.mount_volume("/dev/sdb1", "mnt/usb/test")
        self.assertFalse(result)
        mock_logger.error.assert_called_with("Mount point must be absolute: mnt/usb/test")

    @patch('security.usb_mount.USBGuardManager.is_installed')
    @patch('security.usb_mount.logger')
    def test_mount_volume_usbguard_not_installed(self, mock_logger, mock_is_installed):
        mock_is_installed.return_value = False
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test")
        self.assertFalse(result)
        mock_logger.error.assert_called_with("USBGuard is not installed. Refusing to mount for security reasons.")

    @patch('security.usb_mount.USBGuardManager.is_installed')
    @patch('security.usb_mount.os.makedirs')
    @patch('security.usb_mount.os.path.exists')
    @patch('security.usb_mount.logger')
    def test_mount_volume_makedirs_failure(self, mock_logger, mock_exists, mock_makedirs, mock_is_installed):
        mock_is_installed.return_value = True
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Permission denied")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test")
        self.assertFalse(result)
        mock_logger.error.assert_called_with("Failed to create mount point /mnt/usb/test: Permission denied")

    @patch('security.usb_mount.os.path.normpath')
    @patch('security.usb_mount.logger')
    def test_mount_volume_normalization_error(self, mock_logger, mock_normpath):
        mock_normpath.side_effect = Exception("Normalization failed")
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test")
        self.assertFalse(result)
        mock_logger.error.assert_called_with("Path normalization error: Normalization failed")
