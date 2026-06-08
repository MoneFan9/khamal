import pytest
import subprocess
import os
import stat
from unittest.mock import patch, MagicMock
from core.security.usb_mount import USBMountManager

@pytest.fixture
def mock_stat_blk():
    with patch("core.security.usb_mount.os.stat") as mock_stat:
        mock_result = MagicMock()
        mock_result.st_mode = stat.S_IFBLK
        mock_stat.return_value = mock_result
        yield mock_stat

@pytest.fixture
def mock_usbguard():
    with patch("core.security.usb_mount.USBGuardManager") as mock:
        mock.is_installed.return_value = True
        mock.is_service_active.return_value = True
        mock.list_devices.return_value = "allow id 1234:5678 ... with-devpath \"/dev/sdb1\""
        yield mock

@pytest.mark.django_db
def test_mount_volume_makedirs_oserror(mock_stat_blk, mock_usbguard):
    with patch("core.security.usb_mount.os.path.exists", return_value=False), \
         patch("core.security.usb_mount.os.makedirs", side_effect=OSError("Failed to create")):

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

@pytest.mark.django_db
def test_mount_volume_subprocess_error(mock_stat_blk, mock_usbguard):
    with patch("core.security.usb_mount.os.path.exists", return_value=True), \
         patch("core.security.usb_mount.subprocess.run", side_effect=subprocess.CalledProcessError(1, "mount", stderr="Mount failed")):

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

@pytest.mark.django_db
def test_unmount_volume_subprocess_error():
    with patch("core.security.usb_mount.subprocess.run", side_effect=subprocess.CalledProcessError(1, "umount", stderr="Unmount failed")):

        result = USBMountManager.unmount_volume("/mnt/usb/stick")
        assert result is False

@pytest.mark.django_db
def test_mount_volume_stat_oserror():
    with patch("core.security.usb_mount.os.stat", side_effect=OSError("Stat failed")):
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

@pytest.mark.django_db
def test_mount_volume_usbguard_list_none(mock_stat_blk):
    with patch("core.security.usb_mount.USBGuardManager") as mock:
        mock.is_installed.return_value = True
        mock.is_service_active.return_value = True
        mock.list_devices.return_value = None

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False

@pytest.mark.django_db
def test_usbguard_methods_coverage():
    from core.security.usb_guard import USBGuardManager
    with patch("core.security.usb_guard.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="Error")
        assert USBGuardManager.is_installed() is False
        assert USBGuardManager.is_service_active() is False
        assert USBGuardManager.generate_policy() is None
        assert USBGuardManager.allow_device(1) is False
        assert USBGuardManager.block_device(1) is False
        assert USBGuardManager.list_devices() is None

@pytest.mark.django_db
def test_mount_volume_usbguard_inactive(mock_stat_blk):
    with patch("core.security.usb_mount.USBGuardManager") as mock:
        mock.is_installed.return_value = True
        mock.is_service_active.return_value = False

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is False
