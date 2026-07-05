from django.test import TestCase
from unittest.mock import MagicMock
from core.projects.docker_client import HardenedDockerClient, HardenedContainerCollection

class DockerHardeningTests(TestCase):
    def setUp(self):
        self.mock_inner_client = MagicMock()
        self.mock_containers = MagicMock()
        self.mock_inner_client.containers = self.mock_containers
        self.hardened_client = HardenedDockerClient(self.mock_inner_client)

    def test_run_allowed(self):
        self.hardened_client.containers.run("alpine", command="echo hello")
        self.mock_containers.run.assert_called_once_with("alpine", command="echo hello")

    def test_run_forbidden_privileged(self):
        with self.assertRaises(PermissionError) as cm:
            self.hardened_client.containers.run("alpine", privileged=True)
        self.assertIn("privileged", str(cm.exception))

    def test_create_forbidden_cap_add(self):
        with self.assertRaises(PermissionError) as cm:
            self.hardened_client.containers.create("alpine", cap_add=["NET_ADMIN"])
        self.assertIn("cap_add", str(cm.exception))

    def test_recursive_check_forbidden(self):
        # Even if nested in a dict (though unlikely for these specific params in top level call,
        # the code supports recursive check)
        with self.assertRaises(PermissionError):
            self.hardened_client.containers._check_security_params({"nested": {"privileged": True}})

    def test_direct_api_access_blocked(self):
        with self.assertRaises(PermissionError):
            _ = self.hardened_client.api

        with self.assertRaises(PermissionError):
            _ = self.hardened_client._client

    def test_passthrough_getattr(self):
        # Should pass through to inner client for non-blocked attributes
        self.mock_inner_client.ping.return_value = True
        self.assertTrue(self.hardened_client.ping())

    def test_passthrough_getattribute_containers(self):
        # list() is not explicitly in HardenedContainerCollection but should be passed through
        self.mock_containers.list.return_value = []
        self.assertEqual(self.hardened_client.containers.list(), [])
