import pytest
from unittest.mock import patch, MagicMock
from core.security.usb_mount import USBMountManager
from core.security.usb_guard import USBGuardManager
import os
import subprocess

@pytest.mark.django_db
class TestUSBMountCoverage:

    @patch("core.security.usb_mount.Path.is_block_device")
    @patch("core.security.usb_mount.USBGuardManager.list_devices")
    @patch("core.security.usb_mount.USBGuardManager.is_service_active")
    @patch("core.security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_usbguard_list_failure(self, mock_installed, mock_active, mock_list, mock_block):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = None  # Simulates failure to list devices
        mock_block.return_value = True

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

    @patch("core.security.usb_mount.Path.is_block_device")
    @patch("core.security.usb_mount.USBGuardManager.list_devices")
    @patch("core.security.usb_mount.USBGuardManager.is_service_active")
    @patch("core.security.usb_mount.USBGuardManager.is_installed")
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_mount_volume_makedirs_oserror(self, mock_makedirs, mock_exists, mock_installed, mock_active, mock_list, mock_block):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "allow /dev/sdb1"
        mock_block.return_value = True
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Disk full")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

    def test_validate_paths_normalization_exception(self):
        # We need to trigger an exception in _validate_paths normalization block
        with patch("os.path.normpath", side_effect=Exception("Unexpected error")):
            is_valid, _, _ = USBMountManager._validate_paths("/dev/sdb1", "/mnt/usb/stick")
            assert is_valid is False

    @patch("core.security.usb_mount.Path.is_block_device")
    @patch("core.security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_usbguard_not_installed_coverage(self, mock_installed, mock_block):
        mock_installed.return_value = False
        mock_block.return_value = True
        # We need to satisfy the previous checks
        # is_valid, device_path, mount_point = USBMountManager._validate_paths(device_path, mount_point)
        # We use a path that passes validation
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False
