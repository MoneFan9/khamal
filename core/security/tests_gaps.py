import pytest
from unittest.mock import patch, MagicMock
import subprocess
from core.security.usb_guard import USBGuardManager
from core.security.usb_mount import USBMountManager

@pytest.mark.django_db
class TestSecurityGaps:

    @patch("subprocess.run")
    def test_usb_guard_is_installed_exception(self, mock_run):
        # Coverage for usb_guard.py:17 (CalledProcessError)
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard")
        assert USBGuardManager.is_installed() is False

    @patch("subprocess.run")
    def test_usb_guard_is_service_active_exception(self, mock_run):
        # Coverage for usb_guard.py:26-27 (CalledProcessError)
        mock_run.side_effect = subprocess.CalledProcessError(1, "systemctl")
        assert USBGuardManager.is_service_active() is False

    @patch("subprocess.run")
    def test_usb_guard_generate_policy_failure(self, mock_run):
        # Coverage for usb_guard.py:35-37
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard", stderr="Error")
        assert USBGuardManager.generate_policy() is None

    @patch("subprocess.Popen")
    def test_usb_guard_apply_policy_failure(self, mock_popen):
        # Coverage for usb_guard.py:50-52
        mock_process = MagicMock()
        mock_process.communicate.return_value = (None, None)
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        # This covers the return False at line 49 and implicitly the exception handling
        assert USBGuardManager.apply_policy("allow all") is False

    @patch("subprocess.run")
    def test_usb_guard_list_devices_failure(self, mock_run):
        # Coverage for usb_guard.py:60-62
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard", stderr="Error")
        assert USBGuardManager.list_devices() is None

    @patch("subprocess.run")
    def test_usb_guard_allow_device_failure(self, mock_run):
        # Coverage for usb_guard.py:70-72
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard")
        assert USBGuardManager.allow_device(1) is False

    @patch("subprocess.run")
    def test_usb_guard_block_device_failure(self, mock_run):
        # Coverage for usb_guard.py:80-82
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard")
        assert USBGuardManager.block_device(1) is False

    @patch("core.security.usb_mount.USBGuardManager.is_installed")
    @patch("core.security.usb_mount.os.stat")
    def test_usb_mount_manager_stat_error(self, mock_stat, mock_installed):
        # Coverage for usb_mount.py:78-80
        mock_installed.return_value = True
        mock_stat.side_effect = OSError("Stat failed")
        assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick") is False

    @patch("core.security.usb_mount.USBGuardManager.is_installed")
    def test_usb_mount_manager_not_installed(self, mock_installed):
        # Coverage for usb_mount.py:84-85
        mock_installed.return_value = False
        assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick") is False

    @patch("core.security.usb_mount.USBGuardManager.is_installed")
    @patch("core.security.usb_mount.USBGuardManager.is_service_active")
    @patch("core.security.usb_mount.USBGuardManager.list_devices")
    @patch("core.security.usb_mount.os.stat")
    def test_usb_mount_manager_list_devices_none(self, mock_stat, mock_list, mock_active, mock_installed):
        # Coverage for usb_mount.py:94-96
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = None

        import stat
        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mode = stat.S_IFBLK
        mock_stat.return_value = mock_stat_obj

        assert USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick") is False
