import os
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.conf import settings
from rest_framework import serializers
from projects.serializers import LocalSourceSerializer
from security.usb_mount import USBMountManager

class SecurityHardeningTests(TestCase):

    def test_local_source_serializer_valid_path(self):
        """Test LocalSourceSerializer with a valid path inside BASE_DIR."""
        valid_path = os.path.realpath(os.path.join(str(settings.BASE_DIR), "projects", "my-project"))
        serializer = LocalSourceSerializer(data={
            'host_path': valid_path,
            'container_path': '/app'
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['host_path'], valid_path)

    def test_local_source_serializer_invalid_path_traversal(self):
        """Test LocalSourceSerializer with a path traversal attempt."""
        invalid_path = os.path.join(str(settings.BASE_DIR), "..", "..", "etc", "passwd")
        serializer = LocalSourceSerializer(data={
            'host_path': invalid_path,
            'container_path': '/app'
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('host_path', serializer.errors)

    def test_local_source_serializer_non_absolute_path(self):
        """Test LocalSourceSerializer with a non-absolute path."""
        serializer = LocalSourceSerializer(data={
            'host_path': 'relative/path',
            'container_path': '/app'
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('host_path', serializer.errors)

    def test_local_source_serializer_outside_base_dir(self):
        """Test LocalSourceSerializer with a path outside allowed BASE_DIR."""
        serializer = LocalSourceSerializer(data={
            'host_path': '/etc/passwd',
            'container_path': '/app'
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('host_path', serializer.errors)

    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("subprocess.run")
    def test_usb_mount_valid(self, mock_run, mock_makedirs, mock_exists, mock_usbguard):
        """Test USBMountManager with valid parameters and verify flags."""
        mock_usbguard.return_value = True
        mock_exists.return_value = False
        mock_run.return_value = MagicMock(returncode=0)

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/my-stick")
        self.assertTrue(result)

        # Verify that the correct security flags are passed
        args, kwargs = mock_run.call_args
        command = args[0]
        self.assertIn("-o", command)
        self.assertIn("noexec,nosuid,nodev", command)
        self.assertIn("/dev/sdb1", command)
        self.assertIn("/mnt/usb/my-stick", command)

    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_usb_mount_invalid_device(self, mock_usbguard):
        """Test USBMountManager with an invalid device path (outside /dev)."""
        mock_usbguard.return_value = True
        result = USBMountManager.mount_volume("/etc/passwd", "/mnt/usb/my-stick")
        self.assertFalse(result)

    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_usb_mount_invalid_mount_point(self, mock_usbguard):
        """Test USBMountManager with an invalid mount point (outside /mnt/usb)."""
        mock_usbguard.return_value = True
        result = USBMountManager.mount_volume("/dev/sdb1", "/home/user/my-stick")
        self.assertFalse(result)

    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_usb_mount_prefix_bypass(self, mock_usbguard):
        """Test USBMountManager with prefix bypass attempt (e.g., /mnt/usb-escape)."""
        mock_usbguard.return_value = True
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb-escape")
        self.assertFalse(result)

    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_usb_mount_direct_base(self, mock_usbguard):
        """Test USBMountManager with direct mount on the base directory."""
        mock_usbguard.return_value = True
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb")
        self.assertFalse(result)

    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_usb_mount_no_usbguard(self, mock_usbguard):
        """Test USBMountManager when USBGuard is not installed."""
        mock_usbguard.return_value = False
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/my-stick")
        self.assertFalse(result)
