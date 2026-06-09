import pytest
from unittest.mock import patch, MagicMock
from projects.docker_client import get_docker_client
from security.usb_mount import USBMountManager
import docker
import stat

class TestRegressionSecurityHardening:

    @patch("projects.docker_client.docker.DockerClient")
    def test_docker_host_config_bypass_blocked(self, mock_docker):
        """Test that the hardened Docker client blocks privileged inside host_config."""
        client = get_docker_client()

        # Test nesting inside host_config
        with pytest.raises(PermissionError) as excinfo:
            client.containers.run("alpine", host_config={'privileged': True})
        assert "privileged" in str(excinfo.value)

    @patch("projects.docker_client.docker.DockerClient")
    def test_docker_direct_api_access_blocked(self, mock_docker):
        """Test that direct access to low-level API attributes is blocked."""
        client = get_docker_client()

        with pytest.raises(PermissionError) as excinfo:
            _ = client.api
        assert "Direct access to low-level Docker API 'api' is restricted" in str(excinfo.value)

        with pytest.raises(PermissionError) as excinfo:
            _ = client._client
        assert "Direct access to low-level Docker API '_client' is restricted" in str(excinfo.value)

    @patch("security.usb_mount.os.stat")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    def test_usb_mount_substring_bypass_blocked(self, mock_installed, mock_active, mock_list, mock_stat):
        """Test that device path substring matching doesn't allow bypass (e.g. /dev/sdb matching /dev/sdb1)."""
        mock_installed.return_value = True
        mock_active.return_value = True

        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mode = stat.S_IFBLK
        mock_stat.return_value = mock_stat_obj

        # Scenario: /dev/sdb1 is allowed, but someone tries to mount /dev/sdb (if it were possible)
        # Or more realistically: /dev/sdb is allowed, but /dev/sdb1 is NOT.
        mock_list.return_value = "1: allow id 1234:5678 ... with-devpath \"/dev/sdb\""

        # Trying to mount /dev/sdb1 (which is NOT in the allow list)
        mock_list.return_value = "1: allow id 1234:5678 ... with-devpath \"/dev/sdb1\""

        # Trying to mount /dev/sdb. "/dev/sdb1" is in the line.
        result = USBMountManager.mount_volume("/dev/sdb", "/mnt/usb/stick")
        assert result is False

    @patch("security.usb_mount.os.stat")
    @patch("security.usb_mount.USBGuardManager.list_devices")
    @patch("security.usb_mount.USBGuardManager.is_service_active")
    @patch("security.usb_mount.USBGuardManager.is_installed")
    @patch("security.usb_mount.subprocess.run")
    @patch("security.usb_mount.os.makedirs")
    def test_usb_mount_parent_authorization_valid(self, mock_makedirs, mock_run, mock_installed, mock_active, mock_list, mock_stat):
        """Verify that allowing the parent device allows mounting the partition."""
        mock_installed.return_value = True
        mock_active.return_value = True

        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mode = stat.S_IFBLK
        mock_stat.return_value = mock_stat_obj
        mock_run.return_value = MagicMock(returncode=0)

        # /dev/sdb is allowed
        mock_list.return_value = "1: allow id 1234:5678 ... with-devpath \"/dev/sdb\""

        # Mounting /dev/sdb1 should be allowed
        result = USBMountManager.mount_volume("/dev/sdb1", "/mnt/usb/stick")
        assert result is True
