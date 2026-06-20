import pytest
import os
import subprocess
from unittest.mock import patch, MagicMock
from security.usb_mount import USBMountManager

@pytest.mark.django_db
class TestUSBMountExtended:

    @patch("security.usb_mount.os.path.isabs")
    def test_mount_volume_not_absolute(self, mock_isabs):
        mock_isabs.return_value = False
        result = USBMountManager.mount_volume("/dev/sdb1", "relative/path")
        assert result is False

    @patch("security.usb_mount.os.path.normpath")
    def test_mount_volume_normalization_error(self, mock_normpath):
        mock_normpath.side_effect = Exception("Normalization failed")
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

    @patch("security.usb_mount.os.path.commonpath")
    def test_mount_volume_invalid_device_path(self, mock_commonpath):
        mock_commonpath.return_value = "/not_dev"
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_outside_allowed_base(self, mock_is_installed):
        mock_is_installed.return_value = True
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/other/stick")
        assert result is False

    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_exactly_base(self, mock_is_installed):
        mock_is_installed.return_value = True
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb")
        assert result is False

    @patch("security.usb_mount.os.path.commonpath")
    def test_mount_volume_commonpath_value_error(self, mock_commonpath):
        # First call is for /dev check, return /dev
        # Second call is for /mnt/usb check, raise ValueError
        mock_commonpath.side_effect = ["/dev", ValueError("Invalid paths")]
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_usbguard_not_installed(self, mock_is_installed):
        mock_is_installed.return_value = False
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.os.path.exists")
    @patch("security.usb_mount.os.makedirs")
    def test_mount_volume_makedirs_oserror(self, mock_makedirs, mock_exists, mock_is_installed):
        mock_is_installed.return_value = True
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Permission denied")
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.os.path.exists")
    @patch("security.usb_mount.subprocess.run")
    def test_mount_volume_mount_failure(self, mock_run, mock_exists, mock_list, mock_active, mock_is_installed):
        mock_is_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "allow id 0123:4567 serial 123456 name 'USB' with-interface 08:06:50 with-devpath /dev/sdb1"
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "mount", stderr="Mount failed")
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

    @patch("security.usb_mount.subprocess.run")
    def test_unmount_volume_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "umount", stderr="Unmount failed")
        result = USBMountManager.unmount_volume("/mnt/usb/stick")
        assert result is False
