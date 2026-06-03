import pytest
from unittest.mock import patch, MagicMock
from security.usb_guard import USBGuardManager
from security.usb_mount import USBMountManager
import subprocess
import os
import stat

class TestUSBGuard:
    @patch("subprocess.run")
    def test_is_installed_true(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert USBGuardManager.is_installed() is True

    @patch("subprocess.run")
    def test_is_installed_false(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        assert USBGuardManager.is_installed() is False

    @patch("subprocess.run")
    def test_is_service_active_true(self, mock_run):
        mock_run.return_value = MagicMock(stdout="active\n", returncode=0)
        assert USBGuardManager.is_service_active() is True

    @patch("subprocess.run")
    def test_is_service_active_false(self, mock_run):
        mock_run.return_value = MagicMock(stdout="inactive\n", returncode=0)
        assert USBGuardManager.is_service_active() is False

    @patch("subprocess.run")
    def test_generate_policy_success(self, mock_run):
        mock_run.return_value = MagicMock(stdout="allow id 1234:5678", returncode=0)
        policy = USBGuardManager.generate_policy()
        assert policy == "allow id 1234:5678"

    @patch("subprocess.Popen")
    @patch("subprocess.run")
    def test_apply_policy_success(self, mock_run, mock_popen):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (None, None)
        mock_popen.return_value = mock_process
        mock_run.return_value = MagicMock(returncode=0)

        assert USBGuardManager.apply_policy("allow all") is True
        mock_popen.assert_called_once()
        mock_run.assert_called_with(["sudo", "systemctl", "restart", "usbguard"], check=True)

    @patch("subprocess.run")
    def test_list_devices(self, mock_run):
        mock_run.return_value = MagicMock(stdout="1: allow id 1d6b:0002", returncode=0)
        devices = USBGuardManager.list_devices()
        assert devices == "1: allow id 1d6b:0002"

    @patch("subprocess.run")
    def test_allow_device(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert USBGuardManager.allow_device(1) is True
        mock_run.assert_called_with(["sudo", "usbguard", "allow-device", "1"], check=True)

    @patch("subprocess.run")
    def test_block_device(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert USBGuardManager.block_device(1) is True
        mock_run.assert_called_with(["sudo", "usbguard", "block-device", "1"], check=True)

class TestUSBMount:
    @patch("security.usb_mount.os.stat")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("subprocess.run")
    def test_mount_volume_success(self, mock_run, mock_makedirs, mock_exists, mock_usbguard, mock_active, mock_list, mock_stat):
        mock_usbguard.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "1: allow id 1234:5678 serial \"\" name \"\" hash \"\" parent-hash \"\" via-port \"usb1\" with-interface { 08:06:50 } with-connect-type \"\" with-devpath \"/dev/sdb1\""

        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mode = stat.S_IFBLK
        mock_stat.return_value = mock_stat_obj

        mock_exists.return_value = False
        mock_run.return_value = MagicMock(returncode=0)

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")

        assert result is True
        mock_makedirs.assert_called_once_with("/mnt/usb/stick", exist_ok=True)
        mock_run.assert_called_with(
            ["sudo", "mount", "-o", "noexec,nosuid,nodev", "/dev/sdb1", "/mnt/usb/stick"],
            check=True, capture_output=True, text=True
        )

    @patch("security.usb_mount.os.stat")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("os.path.exists")
    @patch("subprocess.run")
    def test_mount_volume_failure(self, mock_run, mock_exists, mock_usbguard, mock_active, mock_list, mock_stat):
        mock_usbguard.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "allow /dev/sdb1"

        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mode = stat.S_IFBLK
        mock_stat.return_value = mock_stat_obj

        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "mount", stderr="Permission denied")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")

        assert result is False

    @patch("subprocess.run")
    def test_unmount_volume_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert USBMountManager.unmount_volume("/mnt/usb") is True
        mock_run.assert_called_with(
            ["sudo", "umount", "/mnt/usb"],
            check=True, capture_output=True, text=True
        )

    @patch("subprocess.run")
    def test_unmount_volume_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "umount", stderr="Target is busy")
        assert USBMountManager.unmount_volume("/mnt/usb") is False

    def test_mount_volume_invalid_paths(self):
        # Non-absolute mount point
        assert USBMountManager.mount_volume("/dev/sdb1", "mnt/usb/stick") is False
        # Invalid device path (outside /dev)
        assert USBMountManager.mount_volume("/home/user/file", "/mnt/usb/stick") is False
        # Invalid mount point (outside /mnt/usb)
        assert USBMountManager.mount_volume("/dev/sdb1", "/home/user/mount") is False
        # Mounting directly on base
        assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb") is False

    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_usbguard_not_installed(self, mock_installed):
        mock_installed.return_value = False
        assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick") is False

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("os.makedirs")
    @patch("os.path.exists")
    def test_mount_volume_makedirs_failure(self, mock_exists, mock_makedirs, mock_installed):
        mock_installed.return_value = True
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Permission denied")
        assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick") is False

    @patch("os.path.normpath")
    def test_mount_volume_normalization_error(self, mock_normpath):
        mock_normpath.side_effect = Exception("Normalization failed")
        assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick") is False

    @patch("security.usb_mount.os.stat")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_stat_oserror(self, mock_installed, mock_stat):
        mock_installed.return_value = True
        mock_stat.side_effect = OSError("Stat failed")
        assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick") is False

    @patch("security.usb_mount.os.stat")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_not_block_device(self, mock_installed, mock_stat):
        mock_installed.return_value = True
        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mode = stat.S_IFREG # Regular file
        mock_stat.return_value = mock_stat_obj
        assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick") is False

    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.os.stat")
    def test_mount_volume_usbguard_list_failure(self, mock_stat, mock_installed, mock_active, mock_list):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mode = stat.S_IFBLK
        mock_stat.return_value = mock_stat_obj
        mock_list.return_value = None
        assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick") is False

    @patch("os.path.commonpath")
    def test_mount_volume_commonpath_value_error(self, mock_commonpath):
        mock_commonpath.side_effect = ["/dev", ValueError("Invalid paths")]
        assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick") is False
