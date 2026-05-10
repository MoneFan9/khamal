import pytest
from unittest.mock import patch, MagicMock
import subprocess
from core.security.usb_guard import USBGuardManager

def test_is_installed_process_error():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard")
        assert USBGuardManager.is_installed() is False

def test_is_service_active_process_error():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "systemctl")
        assert USBGuardManager.is_service_active() is False

def test_generate_policy_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard", stderr="Error")
        assert USBGuardManager.generate_policy() is None

def test_apply_policy_tee_failure():
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (None, None)
        mock_popen.return_value = mock_process

        assert USBGuardManager.apply_policy("allow all") is False

def test_apply_policy_restart_failure():
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (None, None)
        mock_popen.return_value = mock_process

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "systemctl")
            assert USBGuardManager.apply_policy("allow all") is False

def test_list_devices_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard", stderr="Error")
        assert USBGuardManager.list_devices() is None

def test_allow_device_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard")
        assert USBGuardManager.allow_device(1) is False

def test_block_device_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard")
        assert USBGuardManager.block_device(1) is False
