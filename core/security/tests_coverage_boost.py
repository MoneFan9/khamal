import pytest
import subprocess
import stat
from unittest.mock import patch, MagicMock
from security.usb_mount import USBMountManager
from security.usb_guard import USBGuardManager

@pytest.mark.django_db
class TestSecurityCoverageBoost:

    @patch("security.usb_mount.os.stat")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_stat_oserror(self, mock_installed, mock_active, mock_list, mock_stat):
        """Covers OSError during stat in mount_volume."""
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "allow /dev/sdb1"
        mock_stat.side_effect = OSError("Stat failed")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_mount_volume_list_devices_none(self, mock_installed, mock_active, mock_list):
        """Covers case where list_devices returns None."""
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_list.return_value = None

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

    @patch("security.usb_guard.subprocess.run")
    def test_usb_guard_generate_policy_failure(self, mock_run):
        """Covers CalledProcessError in generate_policy."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard", stderr="Error")
        result = USBGuardManager.generate_policy()
        assert result is None

    @patch("security.usb_guard.subprocess.run")
    def test_usb_guard_list_devices_failure(self, mock_run):
        """Covers CalledProcessError in list_devices."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard", stderr="Error")
        result = USBGuardManager.list_devices()
        assert result is None

    @patch("security.usb_guard.subprocess.run")
    def test_usb_guard_allow_device_failure(self, mock_run):
        """Covers CalledProcessError in allow_device."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard", stderr="Error")
        result = USBGuardManager.allow_device("1")
        assert result is False

    @patch("security.usb_guard.subprocess.run")
    def test_usb_guard_block_device_failure(self, mock_run):
        """Covers CalledProcessError in block_device."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard", stderr="Error")
        result = USBGuardManager.block_device("1")
        assert result is False

    @patch("security.usb_guard.subprocess.Popen")
    def test_usb_guard_apply_policy_failure(self, mock_popen):
        """Covers failure in apply_policy (non-zero return code)."""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (None, None)
        mock_popen.return_value = mock_process

        result = USBGuardManager.apply_policy("allow all")
        assert result is False

    @patch("security.usb_guard.subprocess.Popen")
    def test_usb_guard_apply_policy_exception(self, mock_popen):
        """Covers exception during apply_policy."""
        # Use a real exception that Popen might raise, or just generic Exception
        mock_popen.side_effect = RuntimeError("Failed")
        result = USBGuardManager.apply_policy("allow all")
        assert result is False
