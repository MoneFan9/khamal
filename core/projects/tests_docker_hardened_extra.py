from django.test import TestCase
from .docker_client import HardenedDockerClient, HardenedContainerCollection
from unittest.mock import MagicMock

class DockerExtraCoverageTests(TestCase):
    def test_hardened_container_collection_getattr(self):
        mock_collection = MagicMock()
        mock_collection.list.return_value = []
        hardened = HardenedContainerCollection(mock_collection)
        self.assertEqual(hardened.list(), [])

    def test_hardened_docker_client_getattr(self):
        mock_client = MagicMock()
        mock_client.networks.list.return_value = []
        hardened = HardenedDockerClient(mock_client)
        self.assertEqual(hardened.networks.list(), [])

    def test_hardened_container_collection_recursive_check_non_dict(self):
        mock_collection = MagicMock()
        hardened = HardenedContainerCollection(mock_collection)
        hardened._check_security_params({'volumes': ['/tmp:/tmp']})

    def test_hardened_container_collection_recursive_check_nested(self):
        mock_collection = MagicMock()
        hardened = HardenedContainerCollection(mock_collection)
        with self.assertRaisesRegex(PermissionError, "privileged"):
             hardened._check_security_params({'nested': {'privileged': True}})
