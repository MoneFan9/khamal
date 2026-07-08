import subprocess
from django.test import TestCase
from unittest.mock import patch, MagicMock
from security.usb_mount import USBMountManager
import os

class USBMountBugFixTests(TestCase):

    @patch("security.usb_mount.Path.is_block_device")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("subprocess.run")
    def test_mount_volume_nameerror_fix_verification(self, mock_run, mock_makedirs, mock_exists, mock_list_devices, mock_is_service_active, mock_is_installed, mock_block):
        # Setup mocks to reach the code where normalized_mount was causing NameError
        mock_is_installed.return_value = True
        mock_is_service_active.return_value = True
        mock_list_devices.return_value = "allow device id 1 serial 123 name 'USB' hash 'xyz' parent-hash 'abc' with-interface 08:06:50 /dev/sdb1"
        mock_exists.return_value = False
        mock_block.return_value = True

        # Test the fix
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")

        self.assertTrue(result)
        mock_makedirs.assert_called_once_with("/mnt/usb/stick", exist_ok=True)
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        command = args[0]
        self.assertEqual(command[-1], "/mnt/usb/stick")

    @patch("security.usb_mount.Path.is_block_device")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("subprocess.run")
    def test_usbguard_authorization_regex_robustness(self, mock_run, mock_makedirs, mock_exists, mock_list_devices, mock_is_service_active, mock_is_installed, mock_block):
        mock_is_installed.return_value = True
        mock_is_service_active.return_value = True
        mock_exists.return_value = True # Avoid permission issues with makedirs in tests
        mock_block.return_value = True

        # Scenario 1: Exact match in list-devices (some USBGuard configs show path)
        mock_list_devices.return_value = "allow device id 1 ... /dev/sdb1"
        self.assertTrue(USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick"))

        # Scenario 2: Parent device authorized
        mock_list_devices.return_value = "allow device id 1 ... /dev/sdb"
        self.assertTrue(USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick"))

        # Scenario 3: Device path as part of another path (should NOT authorize)
        mock_list_devices.return_value = "allow device id 1 ... /dev/sdb10"
        self.assertFalse(USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick"))

        # Scenario 4: Another device authorized
        mock_list_devices.return_value = "allow device id 2 ... /dev/sdc1"
        self.assertFalse(USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick"))
