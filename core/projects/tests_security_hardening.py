import pytest
from unittest.mock import patch, MagicMock
from django.conf import settings
from projects.serializers import LocalSourceSerializer
from security.usb_mount import USBMountManager
import os
import stat

class TestSecurityHardening:

    def test_local_source_serializer_valid_path(self):
        """Test LocalSourceSerializer with a valid path inside BASE_DIR."""
        valid_path = os.path.realpath(os.path.join(str(settings.BASE_DIR), "projects", "my-project"))
        serializer = LocalSourceSerializer(data={
            'host_path': valid_path,
            'container_path': '/app'
        })
        assert serializer.is_valid() is True
        assert serializer.validated_data['host_path'] == valid_path

    def test_local_source_serializer_invalid_path_traversal(self):
        """Test LocalSourceSerializer with a path traversal attempt."""
        invalid_path = os.path.join(str(settings.BASE_DIR), "..", "..", "etc", "passwd")
        serializer = LocalSourceSerializer(data={
            'host_path': invalid_path,
            'container_path': '/app'
        })
        assert serializer.is_valid() is False
        assert 'host_path' in serializer.errors

    def test_local_source_serializer_non_absolute_path(self):
        """Test LocalSourceSerializer with a non-absolute path."""
        serializer = LocalSourceSerializer(data={
            'host_path': 'relative/path',
            'container_path': '/app'
        })
        assert serializer.is_valid() is False
        assert 'host_path' in serializer.errors

    def test_local_source_serializer_outside_base_dir(self):
        """Test LocalSourceSerializer with a path outside allowed BASE_DIR."""
        serializer = LocalSourceSerializer(data={
            'host_path': '/etc/passwd',
            'container_path': '/app'
        })
        assert serializer.is_valid() is False
        assert 'host_path' in serializer.errors

    @patch("security.usb_mount.os.stat")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("subprocess.run")
    def test_usb_mount_valid(self, mock_run, mock_makedirs, mock_exists, mock_usbguard, mock_active, mock_list, mock_stat):
        """Test USBMountManager with valid parameters and verify flags."""
        mock_usbguard.return_value = True
        mock_active.return_value = True
        mock_list.return_value = "allow /dev/sdb1"

        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mode = stat.S_IFBLK
        mock_stat.return_value = mock_stat_obj
        mock_exists.return_value = False
        mock_run.return_value = MagicMock(returncode=0)

        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/my-stick")
        assert result is True

        # Verify that the correct security flags are passed
        args, kwargs = mock_run.call_args
        command = args[0]
        assert "-o" in command
        assert "noexec,nosuid,nodev" in command
        assert "/dev/sdb1" in command
        assert "/mnt/usb/my-stick" in command

    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_usb_mount_invalid_device(self, mock_usbguard):
        """Test USBMountManager with an invalid device path (outside /dev)."""
        mock_usbguard.return_value = True
        result = USBMountManager.mount_volume("/etc/passwd", "/mnt/usb/my-stick")
        assert result is False

    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_usb_mount_invalid_mount_point(self, mock_usbguard):
        """Test USBMountManager with an invalid mount point (outside /mnt/usb)."""
        mock_usbguard.return_value = True
        result = USBMountManager.mount_volume("/dev/sdb1", "/home/user/my-stick")
        assert result is False

    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_usb_mount_prefix_bypass(self, mock_usbguard):
        """Test USBMountManager with prefix bypass attempt (e.g., /mnt/usb-escape)."""
        mock_usbguard.return_value = True
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb-escape")
        assert result is False

    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_usb_mount_direct_base(self, mock_usbguard):
        """Test USBMountManager with direct mount on the base directory."""
        mock_usbguard.return_value = True
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb")
        assert result is False

    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_usb_mount_no_usbguard(self, mock_usbguard):
        """Test USBMountManager when USBGuard is not installed."""
        mock_usbguard.return_value = False
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/my-stick")
        assert result is False

    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_usb_mount_inactive_service(self, mock_installed, mock_active):
        """Test USBMountManager when USBGuard service is inactive."""
        mock_installed.return_value = True
        mock_active.return_value = False
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/my-stick")
        assert result is False

    @patch("projects.docker_client.docker.DockerClient")
    def test_docker_privileged_blocked(self, mock_docker):
        """Test that the hardened Docker client blocks privileged=True."""
        from projects.docker_client import get_docker_client
        client = get_docker_client()

        with pytest.raises(PermissionError) as excinfo:
            client.containers.run("alpine", privileged=True)
        assert "privileged" in str(excinfo.value)

    @patch("projects.docker_client.docker.DockerClient")
    def test_docker_cap_add_blocked(self, mock_docker):
        """Test that the hardened Docker client blocks cap_add."""
        from projects.docker_client import get_docker_client
        client = get_docker_client()

        with pytest.raises(PermissionError) as excinfo:
            client.containers.create("alpine", cap_add=["NET_ADMIN"])
        assert "cap_add" in str(excinfo.value)
