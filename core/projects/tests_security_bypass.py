from django.test import TestCase
from unittest.mock import patch, MagicMock
from projects.docker_client import get_docker_client

class DockerSecurityBypassTests(TestCase):
    @patch("projects.docker_client.docker.DockerClient")
    def test_docker_volume_list_bypass_blocked(self, mock_docker):
        """Test that the hardened Docker client blocks docker.sock mount via list."""
        client = get_docker_client()

        # Test dictionary volumes (already protected)
        with self.assertRaises(PermissionError) as cm:
            client.containers.run("alpine", volumes={"/var/run/docker.sock": {"bind": "/docker.sock", "mode": "ro"}})
        self.assertIn("Forbidden host mount detected", str(cm.exception))

        # Test list volumes (new protection)
        with self.assertRaises(PermissionError) as cm:
            client.containers.run("alpine", volumes=["/var/run/docker.sock:/docker.sock:ro"])
        self.assertIn("Forbidden host mount detected", str(cm.exception))

    @patch("projects.docker_client.docker.DockerClient")
    def test_docker_client_access_control(self, mock_docker):
        """Test that direct access to _client is restricted but getattr works for other things."""
        client = get_docker_client()

        # Accessing _client should raise PermissionError
        with self.assertRaises(PermissionError):
            print(client._client)

        # Accessing api should raise PermissionError
        with self.assertRaises(PermissionError):
            print(client.api)

        # Other attributes should work (delegated to _client)
        mock_docker.return_value.version.return_value = {"Version": "1.2.3"}
        self.assertEqual(client.version(), {"Version": "1.2.3"})
