import pytest
from unittest.mock import patch, MagicMock
import subprocess
from security.usb_guard import USBGuardManager

def test_generate_policy_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, ["usbguard", "generate-policy"], stderr="error")
        result = USBGuardManager.generate_policy()
        assert result is None

def test_apply_policy_failure():
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (None, "error")
        mock_popen.return_value = mock_process

        result = USBGuardManager.apply_policy("policy")
        assert result is False

def test_list_devices_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, ["usbguard", "list-devices"], stderr="error")
        result = USBGuardManager.list_devices()
        assert result is None

def test_allow_device_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, ["sudo", "usbguard", "allow-device", "1"])
        result = USBGuardManager.allow_device("1")
        assert result is False

def test_block_device_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, ["sudo", "usbguard", "block-device", "1"])
        result = USBGuardManager.block_device("1")
        assert result is False
