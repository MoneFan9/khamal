import pytest
import subprocess
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from core.security.usb_mount import USBMountManager

@pytest.mark.django_db
class TestUSBMountExtra:

    @patch("core.security.usb_mount.Path.is_block_device")
    @patch("core.security.usb_guard.USBGuardManager.list_devices")
    @patch("core.security.usb_guard.USBGuardManager.is_service_active")
    @patch("core.security.usb_guard.USBGuardManager.is_installed")
    def test_mount_volume_list_devices_none(self, mock_installed, mock_active, mock_list, mock_block):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_block.return_value = True
        mock_list.return_value = None

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

    @patch("core.security.usb_mount.Path.is_block_device")
    @patch("core.security.usb_guard.USBGuardManager.list_devices")
    @patch("core.security.usb_guard.USBGuardManager.is_service_active")
    @patch("core.security.usb_guard.USBGuardManager.is_installed")
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_mount_volume_makedirs_oserror(self, mock_makedirs, mock_exists, mock_installed, mock_active, mock_list, mock_block):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_block.return_value = True
        mock_list.return_value = "allow /dev/sdb1"
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Disk full")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

    @patch("core.security.usb_mount.Path.is_block_device")
    @patch("core.security.usb_guard.USBGuardManager.list_devices")
    @patch("core.security.usb_guard.USBGuardManager.is_service_active")
    @patch("core.security.usb_guard.USBGuardManager.is_installed")
    @patch("os.path.exists")
    @patch("subprocess.run")
    def test_mount_volume_subprocess_error(self, mock_run, mock_exists, mock_installed, mock_active, mock_list, mock_block):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_block.return_value = True
        mock_list.return_value = "allow /dev/sdb1"
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "mount", stderr="Generic error")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

    @patch("core.security.usb_mount.Path.is_block_device")
    @patch("core.security.usb_guard.USBGuardManager.is_service_active")
    @patch("core.security.usb_guard.USBGuardManager.is_installed")
    def test_mount_volume_not_block_device(self, mock_installed, mock_active, mock_block):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_block.return_value = False

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False
