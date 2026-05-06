import pytest
from unittest.mock import patch, MagicMock
from security.usb_mount import USBMountManager
import os

@pytest.mark.django_db
class TestUSBMountExtended:

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.logger")
    def test_mount_volume_non_absolute_mount_point(self, mock_logger, mock_usbguard):
        mock_usbguard.return_value = True
        result = USBMountManager.mount_volume("/dev/sdb1", "mnt/usb/stick")
        assert result is False
        mock_logger.error.assert_any_call("Mount point must be absolute: mnt/usb/stick")

    @patch("security.usb_mount.os.path.normpath")
    @patch("security.usb_mount.logger")
    def test_mount_volume_normalization_error(self, mock_logger, mock_normpath):
        mock_normpath.side_effect = Exception("Normpath error")
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False
        mock_logger.error.assert_called_with("Path normalization error: Normpath error")

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.logger")
    def test_mount_volume_invalid_device_path(self, mock_logger, mock_usbguard):
        mock_usbguard.return_value = True
        result = USBMountManager.mount_volume("/tmp/fake_device", "/mnt/usb/stick")
        assert result is False
        mock_logger.error.assert_any_call("Invalid device path (must be in /dev): /tmp/fake_device")

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.logger")
    def test_mount_volume_invalid_mount_point(self, mock_logger, mock_usbguard):
        mock_usbguard.return_value = True
        result = USBMountManager.mount_volume("/dev/sdb1", "/tmp/invalid_mount")
        assert result is False
        mock_logger.error.assert_any_call("Invalid mount point: /tmp/invalid_mount. Must be within /mnt/usb")

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.logger")
    def test_mount_volume_mount_directly_on_base(self, mock_logger, mock_usbguard):
        mock_usbguard.return_value = True
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb")
        assert result is False
        mock_logger.error.assert_any_call("Cannot mount directly on /mnt/usb")

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.os.path.exists")
    @patch("security.usb_mount.os.makedirs")
    @patch("security.usb_mount.logger")
    def test_mount_volume_makedirs_failure(self, mock_logger, mock_makedirs, mock_exists, mock_usbguard):
        mock_usbguard.return_value = True
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Makedirs failed")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False
        mock_logger.error.assert_any_call("Failed to create mount point /mnt/usb/stick: Makedirs failed")

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.logger")
    @patch("security.usb_mount.os.path.commonpath")
    def test_mount_volume_commonpath_value_error(self, mock_commonpath, mock_logger, mock_usbguard):
        mock_usbguard.return_value = True
        mock_commonpath.side_effect = ["/dev", ValueError("Invalid paths")]

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False
        mock_logger.error.assert_any_call("Invalid paths for commonpath: /mnt/usb, /mnt/usb/stick")

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.logger")
    def test_mount_volume_usbguard_not_installed(self, mock_logger, mock_usbguard):
        mock_usbguard.return_value = False
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False
        mock_logger.error.assert_called_with("USBGuard is not installed. Refusing to mount for security reasons.")
