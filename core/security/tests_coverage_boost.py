import pytest
import subprocess
from unittest.mock import patch, MagicMock
from core.security.usb_guard import USBGuardManager
from core.security.usb_mount import USBMountManager
import os
import stat

@pytest.mark.django_db
def test_usb_guard_apply_policy_exception():
    """
    Test USBGuardManager.apply_policy when subprocess raises an exception.
    Ensures 100% path coverage for the broad exception handler.
    """
    with patch("core.security.usb_guard.subprocess.Popen") as mock_popen:
        mock_popen.side_effect = Exception("Critical system failure")

        # This should be caught by the broad 'except (subprocess.CalledProcessError, Exception)' block
        result = USBGuardManager.apply_policy("allow all")
        assert result is False

@pytest.mark.django_db
def test_usb_mount_stat_os_error():
    """
    Test USBMountManager.mount_volume when os.stat raises OSError.
    """
    with patch("core.security.usb_mount.USBGuardManager.is_installed", return_value=True), \
         patch("core.security.usb_mount.USBGuardManager.is_service_active", return_value=True), \
         patch("core.security.usb_mount.os.stat") as mock_stat:

        mock_stat.side_effect = OSError("Device not found")

        result = USBMountManager.mount_volume("/dev/nonexistent", "/mnt/usb/stick")
        assert result is False

@pytest.mark.django_db
def test_usb_mount_makedirs_os_error():
    """
    Test USBMountManager.mount_volume when os.makedirs raises OSError.
    """
    with patch("core.security.usb_mount.USBGuardManager.is_installed", return_value=True), \
         patch("core.security.usb_mount.USBGuardManager.is_service_active", return_value=True), \
         patch("core.security.usb_mount.USBGuardManager.list_devices", return_value="allow /dev/sdb1"), \
         patch("core.security.usb_mount.os.stat") as mock_stat, \
         patch("core.security.usb_mount.os.path.exists", return_value=False), \
         patch("core.security.usb_mount.os.makedirs") as mock_makedirs:

        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mode = stat.S_IFBLK
        mock_stat.return_value = mock_stat_obj

        mock_makedirs.side_effect = OSError("Permission denied")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

@pytest.mark.django_db
def test_usb_mount_mount_subprocess_error():
    """
    Test USBMountManager.mount_volume when mount command fails.
    """
    with patch("core.security.usb_mount.USBGuardManager.is_installed", return_value=True), \
         patch("core.security.usb_mount.USBGuardManager.is_service_active", return_value=True), \
         patch("core.security.usb_mount.USBGuardManager.list_devices", return_value="allow /dev/sdb1"), \
         patch("core.security.usb_mount.os.stat") as mock_stat, \
         patch("core.security.usb_mount.os.path.exists", return_value=True), \
         patch("core.security.usb_mount.subprocess.run") as mock_run:

        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mode = stat.S_IFBLK
        mock_stat.return_value = mock_stat_obj

        mock_run.side_effect = subprocess.CalledProcessError(1, "mount", stderr="Mounting failed")

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False
