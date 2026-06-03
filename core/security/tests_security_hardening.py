import pytest
from unittest.mock import patch, MagicMock
from security.usb_guard import USBGuardManager
from security.usb_mount import USBMountManager
import subprocess
import os
import stat

class TestSecurityHardening:

    @patch("security.usb_mount.os.stat")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_fails_if_not_block_device(self, mock_installed, mock_active, mock_stat):
        mock_installed.return_value = True
        mock_active.return_value = True

        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mode = stat.S_IFREG
        mock_stat.return_value = mock_stat_obj

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

    @patch("security.usb_mount.os.stat")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_fails_if_service_inactive(self, mock_installed, mock_active, mock_stat):
        mock_installed.return_value = True
        mock_active.return_value = False

        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mode = stat.S_IFBLK
        mock_stat.return_value = mock_stat_obj

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

    @patch("security.usb_mount.os.stat")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_fails_if_device_not_authorized(self, mock_installed, mock_active, mock_list, mock_stat):
        mock_installed.return_value = True
        mock_active.return_value = True

        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mode = stat.S_IFBLK
        mock_stat.return_value = mock_stat_obj

        mock_list.return_value = "1: allow id 1111:2222 ... with-devpath \"/dev/sdc1\""

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

    @patch("security.usb_mount.os.stat")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_fails_if_no_allow_rules(self, mock_installed, mock_active, mock_list, mock_stat):
        mock_installed.return_value = True
        mock_active.return_value = True

        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mode = stat.S_IFBLK
        mock_stat.return_value = mock_stat_obj

        mock_list.return_value = "1: block id 1234:5678 ... with-devpath \"/dev/sdb1\""

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

    @patch("security.usb_mount.os.stat")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.subprocess.run")
    @patch("security.usb_mount.os.makedirs")
    def test_mount_options_applied(self, mock_makedirs, mock_run, mock_installed, mock_active, mock_list, mock_stat):
        mock_installed.return_value = True
        mock_active.return_value = True

        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mode = stat.S_IFBLK
        mock_stat.return_value = mock_stat_obj

        mock_list.return_value = "1: allow id 1234:5678 ... with-devpath \"/dev/sdb1\""
        mock_run.return_value = MagicMock(returncode=0)

        USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")

        assert mock_run.called is True
        args, kwargs = mock_run.call_args
        assert "-o" in args[0]
        assert "noexec,nosuid,nodev" in args[0]
