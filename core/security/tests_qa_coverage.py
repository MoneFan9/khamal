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
