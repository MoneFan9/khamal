import pytest
import subprocess
from unittest.mock import patch, MagicMock
from core.security.usb_guard import USBGuardManager

class TestUSBGuardManager:
    @patch("subprocess.run")
    def test_is_installed_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert USBGuardManager.is_installed() is True
        mock_run.assert_called_once_with(["usbguard", "--version"], capture_output=True, check=True)

    @patch("subprocess.run")
    def test_is_installed_failure(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        assert USBGuardManager.is_installed() is False

    @patch("subprocess.run")
    def test_is_service_active_active(self, mock_run):
        mock_run.return_value = MagicMock(stdout="active\n")
        assert USBGuardManager.is_service_active() is True

    @patch("subprocess.run")
    def test_is_service_active_inactive(self, mock_run):
        mock_run.return_value = MagicMock(stdout="inactive\n")
        assert USBGuardManager.is_service_active() is False

    @patch("subprocess.run")
    def test_generate_policy_success(self, mock_run):
        mock_run.return_value = MagicMock(stdout="policy content", returncode=0)
        assert USBGuardManager.generate_policy() == "policy content"

    @patch("subprocess.run")
    def test_generate_policy_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="error")
        assert USBGuardManager.generate_policy() is None

    @patch("subprocess.Popen")
    @patch("subprocess.run")
    def test_apply_policy_success(self, mock_run, mock_popen):
        mock_process = MagicMock()
        mock_process.communicate.return_value = (None, None)
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        mock_run.return_value = MagicMock(returncode=0)

        assert USBGuardManager.apply_policy("new policy") is True
        mock_popen.assert_called_once()
        mock_process.communicate.assert_called_once_with(input="new policy")

    @patch("subprocess.Popen")
    def test_apply_policy_popen_failure(self, mock_popen):
        mock_process = MagicMock()
        mock_process.communicate.return_value = (None, None)
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        assert USBGuardManager.apply_policy("new policy") is False

    @patch("subprocess.Popen")
    @patch("subprocess.run")
    def test_apply_policy_restart_failure(self, mock_run, mock_popen):
        mock_process = MagicMock()
        mock_process.communicate.return_value = (None, None)
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")

        assert USBGuardManager.apply_policy("new policy") is False

    @patch("subprocess.run")
    def test_list_devices_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="error")
        assert USBGuardManager.list_devices() is None

    @patch("subprocess.run")
    def test_allow_device_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        assert USBGuardManager.allow_device("123") is False

    @patch("subprocess.run")
    def test_block_device_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        assert USBGuardManager.block_device("123") is False

    @patch("subprocess.run")
    def test_list_devices_success(self, mock_run):
        mock_run.return_value = MagicMock(stdout="device list", returncode=0)
        assert USBGuardManager.list_devices() == "device list"

    @patch("subprocess.run")
    def test_allow_device_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert USBGuardManager.allow_device("123") is True
        mock_run.assert_called_once_with(["sudo", "usbguard", "allow-device", "123"], check=True)

    @patch("subprocess.run")
    def test_block_device_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert USBGuardManager.block_device("123") is True
        mock_run.assert_called_once_with(["sudo", "usbguard", "block-device", "123"], check=True)
