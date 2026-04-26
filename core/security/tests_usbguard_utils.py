import subprocess
from unittest.mock import patch, MagicMock
from django.test import SimpleTestCase
from security.usb_guard import USBGuardManager

class USBGuardManagerTests(SimpleTestCase):

    @patch("subprocess.run")
    def test_is_installed_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(USBGuardManager.is_installed())

    @patch("subprocess.run")
    def test_is_installed_failure(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        self.assertFalse(USBGuardManager.is_installed())

    @patch("subprocess.run")
    def test_generate_policy_success(self, mock_run):
        mock_run.return_value = MagicMock(stdout="policy content", returncode=0)
        self.assertEqual(USBGuardManager.generate_policy(), "policy content")

    @patch("subprocess.run")
    def test_generate_policy_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard", stderr="error")
        self.assertIsNone(USBGuardManager.generate_policy())

    @patch("subprocess.run")
    @patch("subprocess.Popen")
    def test_apply_policy_success(self, mock_popen, mock_run):
        mock_process = MagicMock()
        mock_process.communicate.return_value = (None, None)
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        mock_run.return_value = MagicMock(returncode=0)

        self.assertTrue(USBGuardManager.apply_policy("new policy"))
        mock_popen.assert_called_once()
        mock_run.assert_called_once()

    @patch("subprocess.run")
    @patch("subprocess.Popen")
    def test_apply_policy_failure_tee(self, mock_popen, mock_run):
        mock_process = MagicMock()
        mock_process.communicate.return_value = (None, None)
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        self.assertFalse(USBGuardManager.apply_policy("new policy"))
        mock_run.assert_not_called()

    @patch("subprocess.run")
    def test_list_devices_success(self, mock_run):
        mock_run.return_value = MagicMock(stdout="device list", returncode=0)
        self.assertEqual(USBGuardManager.list_devices(), "device list")

    @patch("subprocess.run")
    def test_list_devices_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard", stderr="error")
        self.assertIsNone(USBGuardManager.list_devices())

    @patch("subprocess.run")
    def test_allow_device_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(USBGuardManager.allow_device("1"))

    @patch("subprocess.run")
    def test_allow_device_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard")
        self.assertFalse(USBGuardManager.allow_device("1"))

    @patch("subprocess.run")
    def test_block_device_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(USBGuardManager.block_device("1"))

    @patch("subprocess.run")
    def test_block_device_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard")
        self.assertFalse(USBGuardManager.block_device("1"))
