import unittest
from unittest.mock import patch, MagicMock
import subprocess
import os
from core.security.usb_mount import USBMountManager

class TestUSBMountManagerCoverage(unittest.TestCase):
    def test_unmount_volume_success(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = USBMountManager.unmount_volume("/mnt/usb/test")
            self.assertTrue(result)
            mock_run.assert_called_with(["sudo", "umount", "/mnt/usb/test"], check=True, capture_output=True, text=True)

    def test_unmount_volume_failure(self):
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "umount", stderr="error")
            result = USBMountManager.unmount_volume("/mnt/usb/test")
            self.assertFalse(result)

    def test_validate_paths_invalid_base(self):
        # Mount point outside /mnt/usb
        is_valid, _, _ = USBMountManager._validate_paths("/dev/sdb1", "/tmp/anywhere")
        self.assertFalse(is_valid)

    def test_validate_paths_direct_base(self):
        # Cannot mount directly on /mnt/usb
        is_valid, _, _ = USBMountManager._validate_paths("/dev/sdb1", "/mnt/usb")
        self.assertFalse(is_valid)

    def test_validate_paths_non_absolute(self):
        is_valid, _, _ = USBMountManager._validate_paths("/dev/sdb1", "mnt/usb/test")
        self.assertFalse(is_valid)

    def test_validate_paths_invalid_device(self):
        # Device not in /dev
        is_valid, _, _ = USBMountManager._validate_paths("/home/user/not_a_device", "/mnt/usb/test")
        self.assertFalse(is_valid)

    def test_validate_paths_exception(self):
        with patch("os.path.normpath", side_effect=Exception("error")):
            is_valid, _, _ = USBMountManager._validate_paths("/dev/sdb1", "/mnt/usb/test")
            self.assertFalse(is_valid)

    @patch("pathlib.Path.is_block_device")
    def test_is_block_device(self, mock_is_block):
        mock_is_block.return_value = True
        self.assertTrue(USBMountManager.is_block_device("/dev/sdb1"))

        mock_is_block.return_value = False
        self.assertFalse(USBMountManager.is_block_device("/dev/sdb1"))

    def test_is_block_device_exception(self):
        with patch("pathlib.Path.is_block_device", side_effect=Exception()):
            self.assertFalse(USBMountManager.is_block_device("/dev/sdb1"))

    @patch("core.security.usb_mount.USBGuardManager")
    @patch("core.security.usb_mount.USBMountManager.is_block_device")
    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("subprocess.run")
    def test_mount_volume_success(self, mock_run, mock_makedirs, mock_exists, mock_is_block, mock_usbguard):
        mock_is_block.return_value = True
        mock_usbguard.is_installed.return_value = True
        mock_usbguard.is_service_active.return_value = True
        mock_usbguard.list_devices.return_value = "allow device /dev/sdb1 id 1234:5678"
        mock_exists.return_value = False
        mock_run.return_value = MagicMock(returncode=0)

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test")

        self.assertTrue(result)
        mock_makedirs.assert_called_with("/mnt/usb/test", exist_ok=True)
        mock_run.assert_called()
        args = mock_run.call_args[0][0]
        self.assertIn("noexec,nosuid,nodev", args[3])

    @patch("core.security.usb_mount.USBGuardManager")
    @patch("core.security.usb_mount.USBMountManager.is_block_device")
    def test_mount_volume_not_authorized(self, mock_is_block, mock_usbguard):
        mock_is_block.return_value = True
        mock_usbguard.is_installed.return_value = True
        mock_usbguard.is_service_active.return_value = True
        mock_usbguard.list_devices.return_value = "block device /dev/sdb1 id 1234:5678" # No 'allow'

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test")
        self.assertFalse(result)

    @patch("core.security.usb_mount.USBGuardManager")
    @patch("core.security.usb_mount.USBMountManager.is_block_device")
    def test_mount_volume_usbguard_not_installed(self, mock_is_block, mock_usbguard):
        mock_is_block.return_value = True
        mock_usbguard.is_installed.return_value = False
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test")
        self.assertFalse(result)
