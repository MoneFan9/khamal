import pytest
from unittest.mock import patch, MagicMock
from core.security.usb_guard import USBGuardManager
import subprocess

class TestUSBGuardCoverage:

    @patch("subprocess.run")
    @patch("subprocess.Popen")
    def test_apply_policy_restart_failure(self, mock_popen, mock_run):
        # Setup mock for sudo tee
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (None, None)
        mock_popen.return_value = mock_process

        # Setup mock for sudo systemctl restart usbguard to fail
        mock_run.side_effect = subprocess.CalledProcessError(1, "systemctl restart usbguard")

        result = USBGuardManager.apply_policy("allow all")
        assert result is False

    @patch("subprocess.run")
    def test_list_devices_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard list-devices", stderr="Error")
        result = USBGuardManager.list_devices()
        assert result is None

    @patch("subprocess.run")
    def test_generate_policy_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard generate-policy", stderr="Error")
        result = USBGuardManager.generate_policy()
        assert result is None

    @patch("subprocess.run")
    def test_allow_device_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard allow-device")
        result = USBGuardManager.allow_device(1)
        assert result is False

    @patch("subprocess.run")
    def test_block_device_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard block-device")
        result = USBGuardManager.block_device(1)
        assert result is False

    @patch("subprocess.run")
    def test_is_service_active_filenotfound(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        assert USBGuardManager.is_service_active() is False

    @patch("subprocess.Popen")
    def test_apply_policy_tee_failure(self, mock_popen):
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (None, None)
        mock_popen.return_value = mock_process

        assert USBGuardManager.apply_policy("allow all") is False
