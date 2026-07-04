from django.test import TestCase
from unittest.mock import patch, MagicMock
from core.security.usb_mount import USBMountManager
from core.ai.rag import RCAPromptBuilder
import subprocess
import os

class QACoverageTests(TestCase):

    # --- USBMountManager Tests ---

    @patch("subprocess.run")
    def test_unmount_volume_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = USBMountManager.unmount_volume("/mnt/usb/stick")
        self.assertTrue(result)
        mock_run.assert_called_with(["sudo", "umount", "/mnt/usb/stick"], check=True, capture_output=True, text=True)

    @patch("subprocess.run")
    def test_unmount_volume_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "umount", stderr="device is busy")
        result = USBMountManager.unmount_volume("/mnt/usb/stick")
        self.assertFalse(result)

    @patch("core.security.usb_guard.subprocess.run")
    def test_usb_guard_list_devices_failure(self, mock_run):
        from core.security.usb_guard import USBGuardManager
        mock_run.side_effect = subprocess.CalledProcessError(1, "usbguard", stderr="error")
        self.assertIsNone(USBGuardManager.list_devices())

    def test_validate_paths_relative_mount(self):
        # Should fail as mount_point must be absolute
        is_valid, dev, mount = USBMountManager._validate_paths("/dev/sdb1", "mnt/usb/stick")
        self.assertFalse(is_valid)

    def test_validate_paths_invalid_base(self):
        # Should fail as mount_point is outside /mnt/usb
        is_valid, dev, mount = USBMountManager._validate_paths("/dev/sdb1", "/tmp/stick")
        self.assertFalse(is_valid)

    @patch("os.path.normpath")
    def test_validate_paths_normalization_exception(self, mock_norm):
        mock_norm.side_effect = Exception("error")
        is_valid, dev, mount = USBMountManager._validate_paths("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(is_valid)

    @patch("core.security.usb_mount.Path.is_block_device")
    @patch("core.security.usb_mount.USBGuardManager.is_installed")
    @patch("core.security.usb_mount.USBGuardManager.is_service_active")
    @patch("core.security.usb_mount.USBGuardManager.list_devices")
    def test_mount_volume_usbguard_regex_with_devpath(self, mock_list, mock_active, mock_installed, mock_block):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_block.return_value = True
        # Testing refined regex with with-devpath
        mock_list.return_value = 'allow id 1234:5678 serial "XYZ" name "Stick" hash "..." parent-hash "..." with-interface { ... } with-connect-type "..." with-devpath "/dev/sdb1"'

        with patch("os.makedirs"), patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
            self.assertTrue(result)

    @patch("core.security.usb_mount.Path.is_block_device")
    @patch("core.security.usb_mount.USBGuardManager.is_installed")
    @patch("core.security.usb_mount.USBGuardManager.is_service_active")
    @patch("core.security.usb_mount.USBGuardManager.list_devices")
    def test_mount_volume_usbguard_regex_fails_without_devpath(self, mock_list, mock_active, mock_installed, mock_block):
        mock_installed.return_value = True
        mock_active.return_value = True
        mock_block.return_value = True
        # Fails because it doesn't match the refined regex (missing with-devpath or doesn't match the specific format)
        mock_list.return_value = 'allow id 1234:5678 serial "XYZ" name "Stick" /dev/sdb1'

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        self.assertFalse(result)

    # --- RCAPromptBuilder Tests ---

    def test_rca_prompt_builder_tools_enabled(self):
        builder = RCAPromptBuilder(enable_tools=True)
        self.assertEqual(builder.system_prompt, builder.TOOL_ENABLED_SYSTEM_PROMPT)
        self.assertIn("propose_fix", builder.system_prompt)

    def test_rca_prompt_builder_repr_custom_prompt(self):
        builder = RCAPromptBuilder(system_prompt="Custom")
        self.assertIn("custom_system_prompt=True", repr(builder))

    def test_rca_prompt_builder_format_logs_none(self):
        builder = RCAPromptBuilder()
        with self.assertRaises(ValueError):
             builder.build_prompt(None)

    def test_rca_prompt_builder_format_logs_with_none_elements(self):
        builder = RCAPromptBuilder()
        prompt = builder.build_prompt(["log1", None, "log2"])
        self.assertIn("log1\nlog2", prompt.user)
