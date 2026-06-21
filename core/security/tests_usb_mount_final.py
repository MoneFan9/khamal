import pytest
import subprocess
import os
from unittest.mock import patch, MagicMock
from core.security.usb_mount import USBMountManager

class TestUSBMountManagerFinal:
    def test_validate_paths_success(self):
        valid, dev, mnt = USBMountManager._validate_paths("/dev/sdb1", "/mnt/usb/stick")
        assert valid is True
        assert dev == "/dev/sdb1"
        assert mnt == "/mnt/usb/stick"

    def test_validate_paths_not_absolute_mount(self):
        valid, _, _ = USBMountManager._validate_paths("/dev/sdb1", "relative/path")
        assert valid is False

    def test_validate_paths_not_in_dev(self):
        valid, _, _ = USBMountManager._validate_paths("/etc/passwd", "/mnt/usb/stick")
        assert valid is False

    def test_validate_paths_outside_mnt_usb(self):
        valid, _, _ = USBMountManager._validate_paths("/dev/sdb1", "/home/user")
        assert valid is False

    def test_validate_paths_mount_on_base(self):
        valid, _, _ = USBMountManager._validate_paths("/dev/sdb1", "/mnt/usb")
        assert valid is False

    @patch("core.security.usb_mount.USBGuardManager")
    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("subprocess.run")
    def test_mount_volume_success_with_parent(self, mock_run, mock_makedirs, mock_exists, mock_usbguard):
        mock_usbguard.is_installed.return_value = True
        mock_usbguard.is_service_active.return_value = True
        # Mocking parent device authorization (/dev/sdb instead of /dev/sdb1)
        mock_usbguard.list_devices.return_value = "allow ... with-devpath /dev/sdb\n"

        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test") is True

    @patch("core.security.usb_mount.USBGuardManager")
    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("subprocess.run")
    def test_mount_volume_success(self, mock_run, mock_makedirs, mock_exists, mock_usbguard):
        mock_usbguard.is_installed.return_value = True
        mock_usbguard.is_service_active.return_value = True
        mock_usbguard.list_devices.return_value = "allow id 123 serial 1234 name ... with-interface ... with-devpath /dev/sdb1\n"

        mock_exists.return_value = False
        mock_run.return_value = MagicMock(returncode=0)

        assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test") is True

        mock_makedirs.assert_called_once()
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "mount" in args
        assert "noexec,nosuid,nodev" in args

    @patch("core.security.usb_mount.USBGuardManager")
    def test_mount_volume_not_authorized(self, mock_usbguard):
        mock_usbguard.is_installed.return_value = True
        mock_usbguard.is_service_active.return_value = True
        mock_usbguard.list_devices.return_value = "block id 123 ... /dev/sdb1\n"

        assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test") is False

    @patch("subprocess.run")
    def test_unmount_volume_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert USBMountManager.unmount_volume("/mnt/usb/test") is True
        mock_run.assert_called_once_with(["sudo", "umount", "/mnt/usb/test"], check=True, capture_output=True, text=True)

    @patch("subprocess.run")
    def test_unmount_volume_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "umount", stderr="error")
        assert USBMountManager.unmount_volume("/mnt/usb/test") is False

    @patch("core.security.usb_mount.USBGuardManager")
    def test_mount_volume_usbguard_not_active(self, mock_usbguard):
        mock_usbguard.is_installed.return_value = True
        mock_usbguard.is_service_active.return_value = False
        assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test") is False

    @patch("core.security.usb_mount.USBGuardManager")
    def test_mount_volume_usbguard_list_failure(self, mock_usbguard):
        mock_usbguard.is_installed.return_value = True
        mock_usbguard.is_service_active.return_value = True
        mock_usbguard.list_devices.return_value = None
        assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test") is False

    @patch("core.security.usb_mount.USBGuardManager")
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_mount_volume_makedirs_failure(self, mock_makedirs, mock_exists, mock_usbguard):
        mock_usbguard.is_installed.return_value = True
        mock_usbguard.is_service_active.return_value = True
        mock_usbguard.list_devices.return_value = "allow ... /dev/sdb1\n"
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Permission denied")
        assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test") is False

    def test_validate_paths_normalization_error(self):
        # Triggering an exception in normpath is hard, but we can mock it
        with patch("os.path.normpath", side_effect=Exception("norm error")):
            valid, _, _ = USBMountManager._validate_paths("/dev/sdb1", "/mnt/usb/test")
            assert valid is False

    def test_validate_paths_commonpath_error(self):
        # We need to make sure the first call to commonpath (for /dev) succeeds
        # and the second one (for /mnt/usb) fails.
        original_commonpath = os.path.commonpath
        def side_effect(paths):
            if "/mnt/usb" in paths:
                raise ValueError("common error")
            return original_commonpath(paths)

        with patch("os.path.commonpath", side_effect=side_effect):
            valid, _, _ = USBMountManager._validate_paths("/dev/sdb1", "/mnt/usb/test")
            assert valid is False
