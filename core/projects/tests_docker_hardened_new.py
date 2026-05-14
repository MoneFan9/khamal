import unittest
from unittest.mock import MagicMock
from core.projects.docker_client import HardenedDockerClient, HardenedContainerCollection

class TestHardenedDockerClient(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.hardened_client = HardenedDockerClient(self.mock_client)

    def test_restricted_attributes(self):
        """Verify that direct access to restricted attributes raises PermissionError."""
        with self.assertRaises(PermissionError) as cm:
            _ = self.hardened_client.api
        self.assertIn("Direct access to low-level Docker API 'api' is restricted", str(cm.exception))

        with self.assertRaises(PermissionError) as cm:
            _ = self.hardened_client._client
        self.assertIn("Direct access to low-level Docker API '_client' is restricted", str(cm.exception))

    def test_delegation_works(self):
        """Verify that non-restricted attributes are correctly delegated to the underlying client."""
        self.mock_client.version.return_value = {"Version": "1.2.3"}
        self.assertEqual(self.hardened_client.version(), {"Version": "1.2.3"})

    def test_forbidden_parameters_in_run(self):
        """Verify that forbidden parameters in containers.run raise PermissionError."""
        with self.assertRaises(PermissionError) as cm:
            self.hardened_client.containers.run("nginx", privileged=True)
        self.assertIn("Use of forbidden Docker parameter 'privileged'", str(cm.exception))

        with self.assertRaises(PermissionError) as cm:
            self.hardened_client.containers.run("nginx", cap_add=["SYS_ADMIN"])
        self.assertIn("Use of forbidden Docker parameter 'cap_add'", str(cm.exception))

    def test_forbidden_parameters_in_create(self):
        """Verify that forbidden parameters in containers.create raise PermissionError."""
        with self.assertRaises(PermissionError) as cm:
            self.hardened_client.containers.create("nginx", devices=["/dev/sda:/dev/sda"])
        self.assertIn("Use of forbidden Docker parameter 'devices'", str(cm.exception))

    def test_allowed_parameters_work(self):
        """Verify that allowed parameters are passed to the underlying collection."""
        self.mock_client.containers.run.return_value = MagicMock()
        self.hardened_client.containers.run("nginx", detach=True, ports={'80/tcp': 8080})
        self.mock_client.containers.run.assert_called_with("nginx", detach=True, ports={'80/tcp': 8080})

        self.mock_client.containers.create.return_value = MagicMock()
        self.hardened_client.containers.create("nginx", command="sleep 10")
        self.mock_client.containers.create.assert_called_with("nginx", command="sleep 10")

    def test_recursive_parameter_check(self):
        """Verify that forbidden parameters are detected even when nested (e.g. in host_config)."""
        with self.assertRaises(PermissionError) as cm:
            # Simulate nested structure sometimes used in lower level APIs or future extensions
            self.hardened_client.containers.run("nginx", host_config={'privileged': True, 'security_opt': ['no-new-privileges']})
        # Note: the current implementation checks keys in dicts recursively
        self.assertIn("use of forbidden docker parameter 'privileged'", str(cm.exception).lower())

        # Test non-dict value for recursive check (edge case for coverage)
        self.hardened_client.containers.run("nginx", simple_param="value")
