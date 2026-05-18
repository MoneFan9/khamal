import pytest
from unittest.mock import MagicMock
from security.usb_mount import USBMountManager

@pytest.fixture
def mock_path(mocker):
    return mocker.patch("security.usb_mount.Path")

@pytest.fixture
def mock_usbguard(mocker):
    mocker.patch("security.usb_guard.USBGuardManager.is_installed", return_value=True)
    mocker.patch("security.usb_guard.USBGuardManager.is_service_active", return_value=True)
    return mocker.patch("security.usb_guard.USBGuardManager.list_devices")

def test_mount_fails_if_not_block_device(mock_path, mock_usbguard):
    mock_path.return_value.is_block_device.return_value = False
    result = USBMountManager.mount_volume("/dev/not_a_block", "/mnt/usb/test")
    assert result is False
    mock_path.return_value.is_block_device.assert_called_once()

def test_mount_success_if_block_device(mock_path, mock_usbguard, mocker):
    mock_path.return_value.is_block_device.return_value = True
    mock_usbguard.return_value = "allow /dev/sdb1"
    mocker.patch("os.path.exists", return_value=True)
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = MagicMock(returncode=0)

    result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/test")
    assert result is True
    mock_path.return_value.is_block_device.assert_called_once()
