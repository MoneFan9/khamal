import os
from unittest.mock import patch, MagicMock
from django.test import TestCase
from projects.docker_client import get_docker_client

class DockerHardeningReinforcementTests(TestCase):

    @patch("projects.docker_client.docker.DockerClient")
    def test_docker_forbidden_params(self, mock_docker):
        client = get_docker_client()

        forbidden = ['network_mode', 'ipc_mode', 'uts_mode', 'sysctls']
        for param in forbidden:
            with self.assertRaises(PermissionError) as cm:
                client.containers.run("alpine", **{param: "host"})
            self.assertIn(param, str(cm.exception))

    @patch("projects.docker_client.docker.DockerClient")
    def test_docker_restricted_volumes_dict(self, mock_docker):
        client = get_docker_client()

        restricted_paths = ['/', '/etc', '/var/run/docker.sock', '/root', '/home']
        for path in restricted_paths:
            with self.assertRaises(PermissionError) as cm:
                client.containers.run("alpine", volumes={path: {'bind': '/mnt', 'mode': 'rw'}})
            self.assertIn("restricted host path", str(cm.exception))

    @patch("projects.docker_client.docker.DockerClient")
    def test_docker_restricted_volumes_list(self, mock_docker):
        client = get_docker_client()

        with self.assertRaises(PermissionError) as cm:
            client.containers.run("alpine", volumes=['/etc/shadow:/etc/shadow:ro'])
        self.assertIn("restricted host path", str(cm.exception))

    @patch("projects.docker_client.docker.DockerClient")
    def test_docker_path_traversal_volume(self, mock_docker):
        client = get_docker_client()

        # Try to bypass with ..
        with self.assertRaises(PermissionError) as cm:
            client.containers.run("alpine", volumes={'/tmp/../etc/passwd': {'bind': '/passwd'}})
        self.assertIn("restricted host path", str(cm.exception))

    @patch("projects.docker_client.docker.DockerClient")
    def test_docker_allowed_volume(self, mock_docker):
        client = get_docker_client()
        mock_run = mock_docker.return_value.containers.run

        # This should NOT raise an error (assuming /tmp is not restricted)
        # Note: In my implementation I restricted /var, and /tmp is often /var/tmp or similar,
        # but let's use a path that is definitely not restricted if possible.
        # Actually /tmp is not in my restricted_paths list.
        client.containers.run("alpine", volumes={'/tmp/my-data': {'bind': '/data'}})
        self.assertTrue(mock_run.called)
