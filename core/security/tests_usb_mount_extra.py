import pytest
import os
import subprocess
from unittest.mock import patch, MagicMock
from security.usb_mount import USBMountManager

@pytest.mark.django_db
class TestUSBMountExtra:
    @patch("core.security.usb_mount.Path.is_block_device")
    @patch("core.security.usb_mount.USBGuardManager.list_devices")
    @patch("core.security.usb_mount.USBGuardManager.is_service_active")
    @patch("core.security.usb_mount.USBGuardManager.is_installed")
    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("subprocess.run")
    def test_mount_volume_not_block_device(self, mock_run, mock_makedirs, mock_exists, mock_usbguard, mock_active, mock_list, mock_block):
        mock_block.return_value = False
        mock_usbguard.return_value = True
        mock_active.return_value = True

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

    @patch("core.security.usb_mount.Path.is_block_device")
    @patch("core.security.usb_mount.USBGuardManager.list_devices")
    @patch("core.security.usb_mount.USBGuardManager.is_service_active")
    @patch("core.security.usb_mount.USBGuardManager.is_installed")
    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("subprocess.run")
    def test_mount_volume_usbguard_service_inactive(self, mock_run, mock_makedirs, mock_exists, mock_usbguard, mock_active, mock_list, mock_block):
        mock_block.return_value = True
        mock_usbguard.return_value = True
        mock_active.return_value = False

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

    @patch("core.security.usb_mount.Path.is_block_device")
    @patch("core.security.usb_mount.USBGuardManager.list_devices")
    @patch("core.security.usb_mount.USBGuardManager.is_service_active")
    @patch("core.security.usb_mount.USBGuardManager.is_installed")
    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("subprocess.run")
    def test_mount_volume_list_devices_none(self, mock_run, mock_makedirs, mock_exists, mock_usbguard, mock_active, mock_list, mock_block):
        mock_block.return_value = True
        mock_usbguard.return_value = True
        mock_active.return_value = True
        mock_list.return_value = None

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

    @patch("core.security.usb_mount.Path.is_block_device")
    @patch("core.security.usb_mount.USBGuardManager.list_devices")
    @patch("core.security.usb_mount.USBGuardManager.is_service_active")
    @patch("core.security.usb_mount.USBGuardManager.is_installed")
    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("subprocess.run")
    def test_mount_volume_not_authorized(self, mock_run, mock_makedirs, mock_exists, mock_usbguard, mock_active, mock_list, mock_block):
        mock_block.return_value = True
        mock_usbguard.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "allow /dev/other"

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False
