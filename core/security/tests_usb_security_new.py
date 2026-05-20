import pytest
from unittest.mock import patch, MagicMock
import subprocess
import os
from pathlib import Path
from security.usb_mount import USBMountManager

@pytest.mark.django_db
class TestUSBMountSecurityNew:

    @patch("security.usb_mount.Path.is_block_device")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.os.path.exists")
    @patch("security.usb_mount.subprocess.run")
    def test_mount_volume_is_block_device_check(self, mock_run, mock_exists, mock_list, mock_active, mock_installed, mock_is_block):
        # Setup mocks for a successful path validation but failing block device check
        mock_is_block.return_value = False
        mock_installed.return_value = True
        mock_active.return_value = True

        # Test that it fails when not a block device
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False
        mock_is_block.assert_called_once()
        mock_run.assert_not_called()

    @patch("security.usb_mount.Path.is_block_device")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.os.path.exists")
    @patch("security.usb_mount.subprocess.run")
    def test_mount_volume_success_flow_and_nameerror_fix(self, mock_run, mock_exists, mock_list, mock_active, mock_installed, mock_is_block):
        mock_is_block.return_value = True
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "allow id 0123:4567 serial 1234 name 'USB Drive' hash '...' parent-hash '...' via-port '...' with-interface { ... } /dev/sdb1"
        mock_exists.return_value = True

        # Test successful mount and verify no NameError (normalized_mount vs mount_point)
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is True

        # Verify mount command options
        args, kwargs = mock_run.call_args
        command = args[0]
        assert "noexec,nosuid,nodev" in command[3]
        assert "/mnt/usb/stick" in command
