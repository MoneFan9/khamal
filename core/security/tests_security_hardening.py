from django.test import TestCase
from unittest.mock import patch, MagicMock
from security.usb_guard import USBGuardManager
from security.usb_mount import USBMountManager
import subprocess

import stat

class SecurityHardeningTests(TestCase):

    @patch("security.usb_mount.os.stat")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_fails_if_not_block_device(self, mock_installed, mock_active, mock_list, mock_stat):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "1: allow id 1234:5678 ... with-devpath \"/dev/sdb1\""
        # Mocking stat result to not be a block device
        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mode = 0  # Regular file, not a block device
        mock_stat.return_value = mock_stat_obj

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.os.stat")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_fails_if_service_inactive(self, mock_installed, mock_active, mock_stat):
        mock_installed.return_value = True
        mock_active.return_value = False

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.os.stat")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_fails_if_device_not_authorized(self, mock_installed, mock_active, mock_list, mock_stat):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "1: allow id 1111:2222 ... with-devpath \"/dev/sdc1\""

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.os.stat")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_fails_if_no_allow_rules(self, mock_installed, mock_active, mock_list, mock_stat):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "1: block id 1234:5678 ... with-devpath \"/dev/sdb1\""

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    @patch("security.usb_mount.os.stat")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.subprocess.run")
    @patch("security.usb_mount.os.makedirs")
    def test_mount_options_applied(self, mock_makedirs, mock_run, mock_installed, mock_active, mock_list, mock_stat):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "1: allow id 1234:5678 ... with-devpath \"/dev/sdb1\""
        mock_run.return_value = MagicMock(returncode=0)

        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mode = stat.S_IFBLK # It's a block device
        mock_stat.return_value = mock_stat_obj

        USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")

        self.assertTrue(mock_run.called, "subprocess.run was not called")
        args, kwargs = mock_run.call_args
        self.assertIn("-o", args[0])
        self.assertIn("noexec,nosuid,nodev", args[0])
