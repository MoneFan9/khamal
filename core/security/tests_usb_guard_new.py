import pytest
from unittest.mock import patch, MagicMock
import subprocess
from security.usb_guard import USBGuardManager

@patch("subprocess.run")
def test_is_installed(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    assert USBGuardManager.is_installed() is True

    mock_run.side_effect = FileNotFoundError
    assert USBGuardManager.is_installed() is False

@patch("subprocess.run")
def test_is_service_active(mock_run):
    mock_run.return_value = MagicMock(stdout="active\n")
    assert USBGuardManager.is_service_active() is True

    mock_run.return_value = MagicMock(stdout="inactive\n")
    assert USBGuardManager.is_service_active() is False

    mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
    assert USBGuardManager.is_service_active() is False

@patch("subprocess.run")
def test_generate_policy(mock_run):
    mock_run.return_value = MagicMock(stdout="policy content", returncode=0)
    assert USBGuardManager.generate_policy() == "policy content"

    mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="error")
    assert USBGuardManager.generate_policy() is None

@patch("subprocess.run")
@patch("subprocess.Popen")
def test_apply_policy(mock_popen, mock_run):
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate.return_value = (None, None)
    mock_popen.return_value = mock_process

    mock_run.return_value = MagicMock(returncode=0)

    assert USBGuardManager.apply_policy("new policy") is True
    mock_popen.assert_called_once()
    mock_run.assert_called_with(["sudo", "systemctl", "restart", "usbguard"], check=True)

@patch("subprocess.run")
def test_list_devices(mock_run):
    mock_run.return_value = MagicMock(stdout="device list", returncode=0)
    assert USBGuardManager.list_devices() == "device list"

@patch("subprocess.run")
def test_allow_device(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    assert USBGuardManager.allow_device("123") is True
    mock_run.assert_called_with(["sudo", "usbguard", "allow-device", "123"], check=True)

@patch("subprocess.run")
def test_block_device(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    assert USBGuardManager.block_device("123") is True
    mock_run.assert_called_with(["sudo", "usbguard", "block-device", "123"], check=True)
