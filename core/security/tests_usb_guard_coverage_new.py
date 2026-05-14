from django.test import TestCase
from unittest.mock import patch, MagicMock
from core.security.usb_guard import USBGuardManager
import subprocess

class USBGuardCoverageTests(TestCase):

    @patch("core.security.usb_guard.subprocess.run")
    def test_list_devices_failure(self, mock_run):
        """Verify failure when usbguard list-devices fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard")
        devices = USBGuardManager.list_devices()
        self.assertIsNone(devices)

    @patch("core.security.usb_guard.subprocess.run")
    def test_allow_device_failure(self, mock_run):
        """Verify failure when usbguard allow-device fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard")
        result = USBGuardManager.allow_device("1")
        self.assertFalse(result)

    @patch("core.security.usb_guard.subprocess.run")
    def test_block_device_failure(self, mock_run):
        """Verify failure when usbguard block-device fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard")
        result = USBGuardManager.block_device("1")
        self.assertFalse(result)

    @patch("core.security.usb_guard.subprocess.run")
    def test_generate_policy_failure(self, mock_run):
        """Verify failure when usbguard generate-policy fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard")
        policy = USBGuardManager.generate_policy()
        self.assertIsNone(policy)

    @patch("core.security.usb_guard.subprocess.Popen")
    def test_apply_policy_popen_failure(self, mock_popen):
        """Verify failure when Popen fails in apply_policy."""
        mock_popen.side_effect = subprocess.CalledProcessError(1, "sudo")
        result = USBGuardManager.apply_policy("allow all")
        self.assertFalse(result)

    @patch("core.security.usb_guard.subprocess.Popen")
    def test_apply_policy_process_failure(self, mock_popen):
        """Verify failure when the policy application process returns non-zero."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"", b"Error")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        result = USBGuardManager.apply_policy("allow all")
        self.assertFalse(result)
