from django.test import TestCase
from unittest.mock import patch, MagicMock
from core.security.usb_mount import USBMountManager
import subprocess
import os

class USBMountCoverageTests(TestCase):

    @patch("core.security.usb_mount.USBGuardManager.list_devices")
    @patch("core.security.usb_mount.USBGuardManager.is_service_active")
    @patch("core.security.usb_mount.USBGuardManager.is_installed")
    def test_mount_fails_if_list_devices_none(self, mock_installed, mock_active, mock_list):
        """Verify failure when USBGuard fails to list devices."""
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = None

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("core.security.usb_mount.USBGuardManager.list_devices")
    @patch("core.security.usb_mount.USBGuardManager.is_service_active")
    @patch("core.security.usb_mount.USBGuardManager.is_installed")
    @patch("core.security.usb_mount.os.path.exists")
    @patch("core.security.usb_mount.os.makedirs")
    def test_mount_makedirs_failure(self, mock_makedirs, mock_exists, mock_installed, mock_active, mock_list):
        """Verify failure when creating the mount point fails."""
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "allow /dev/sdb1"
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Permission denied")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("core.security.usb_mount.USBGuardManager.list_devices")
    @patch("core.security.usb_mount.USBGuardManager.is_service_active")
    @patch("core.security.usb_mount.USBGuardManager.is_installed")
    @patch("core.security.usb_mount.subprocess.run")
    @patch("core.security.usb_mount.os.path.exists")
    def test_mount_subprocess_failure(self, mock_exists, mock_run, mock_installed, mock_active, mock_list):
        """Verify failure when the mount command itself fails."""
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "allow /dev/sdb1"
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "mount", stderr="Special error")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    def test_validate_paths_non_absolute_mount(self):
        """Verify validation failure for non-absolute mount point."""
        is_valid, _, _ = USBMountManager._validate_paths("/dev/sdb1", "mnt/usb/stick")
        self.assertFalse(is_valid)

    def test_validate_paths_invalid_device(self):
        """Verify validation failure for device path outside /dev."""
        is_valid, _, _ = USBMountManager._validate_paths("/tmp/fake_dev", "/mnt/usb/stick")
        self.assertFalse(is_valid)

    def test_validate_paths_invalid_mount_base(self):
        """Verify validation failure for mount point outside /mnt/usb."""
        is_valid, _, _ = USBMountManager._validate_paths("/dev/sdb1", "/tmp/mount")
        self.assertFalse(is_valid)

    def test_validate_paths_mount_on_base(self):
        """Verify validation failure when mounting directly on /mnt/usb."""
        is_valid, _, _ = USBMountManager._validate_paths("/dev/sdb1", "/mnt/usb")
        self.assertFalse(is_valid)
