from django.test import TestCase
from unittest.mock import MagicMock, patch
from core.projects.docker_client import get_docker_client
import pytest

class DockerHardeningExtraTests(TestCase):
    @patch("core.projects.docker_client.docker.DockerClient")
    def test_docker_case_insensitive_blocked(self, mock_docker_class):
        """Test that the hardened Docker client blocks forbidden parameters regardless of case."""
        mock_client = MagicMock()
        mock_docker_class.return_value = mock_client

        from django.conf import settings
        with patch.object(settings, 'DOCKER_URL', 'http://localhost:2375'):
            client = get_docker_client()

            # Test lowercase (already should work)
            with self.assertRaises(PermissionError) as cm:
                client.containers.run("alpine", privileged=True)
            self.assertIn("privileged", str(cm.exception))

            # Test CamelCase (the fix)
            with self.assertRaises(PermissionError) as cm:
                client.containers.run("alpine", host_config={'Privileged': True})
            self.assertIn("Privileged", str(cm.exception))

            # Test another forbidden param
            with self.assertRaises(PermissionError) as cm:
                client.containers.create("alpine", cap_add=["SYS_ADMIN"])
            self.assertIn("cap_add", str(cm.exception))

            # Test CamelCase variant for cap_add
            with self.assertRaises(PermissionError) as cm:
                client.containers.create("alpine", host_config={'CapAdd': ["SYS_ADMIN"]})
            self.assertIn("CapAdd", str(cm.exception))

            # Test another one like SecurityOpt
            with self.assertRaises(PermissionError) as cm:
                client.containers.run("alpine", host_config={'SecurityOpt': ["seccomp=unconfined"]})
            self.assertIn("SecurityOpt", str(cm.exception))
