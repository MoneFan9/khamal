import pytest
from unittest.mock import patch, MagicMock
import subprocess
from core.security.usb_guard import USBGuardManager

def test_generate_policy_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard", stderr="Error")
        policy = USBGuardManager.generate_policy()
        assert policy is None

def test_apply_policy_popen_failure():
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.side_effect = Exception("Popen failed")
        with pytest.raises(Exception, match="Popen failed"):
            USBGuardManager.apply_policy("allow all")

def test_apply_policy_systemctl_failure():
    with patch("subprocess.Popen") as mock_popen, patch("subprocess.run") as mock_run:
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (None, None)
        mock_popen.return_value = mock_process

        mock_run.side_effect = subprocess.CalledProcessError(1, "systemctl")

        result = USBGuardManager.apply_policy("allow all")
        assert result is False

def test_list_devices_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard")
        devices = USBGuardManager.list_devices()
        assert devices is None

def test_allow_device_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard")
        result = USBGuardManager.allow_device(1)
        assert result is False

def test_block_device_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard")
        result = USBGuardManager.block_device(1)
        assert result is False
