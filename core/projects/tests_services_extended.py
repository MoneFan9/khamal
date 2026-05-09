from django.test import TestCase
from django.contrib.auth import get_user_model
from projects.models import Project, Deployment
from projects.services import (
    ensure_project_network, stop_container, restart_container,
    remove_container, get_deployment_logs
)
from unittest.mock import patch, MagicMock
import docker

User = get_user_model()

class ProjectsServicesExtendedTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser_proj", password="password")
        self.project = Project.objects.create(name="Test Project Proj", owner=self.user, network_id="existing-net")
        self.deployment = Deployment.objects.create(
            project=self.project,
            container_id="existing-container",
            status=Deployment.Status.RUNNING,
            container_port=8000
        )

    @patch('projects.services.get_docker_client')
    @patch('projects.services.logger')
    def test_ensure_project_network_recreate_if_not_found(self, mock_logger, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # client.networks.get raises NotFound when network_id exists in DB but not in Docker
        mock_client.networks.get.side_effect = docker.errors.NotFound("Network not found")

        # Mock network creation
        mock_network = MagicMock()
        mock_network.id = "new-network-id"
        mock_client.networks.list.return_value = []
        mock_client.networks.create.return_value = mock_network

        network_id = ensure_project_network(self.project)

        self.assertEqual(network_id, "new-network-id")
        mock_logger.warning.assert_called()
        self.project.refresh_from_db()
        self.assertEqual(self.project.network_id, "new-network-id")

    @patch('projects.services.get_docker_client')
    def test_stop_container_failure(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = Exception("Docker stop error")

        with self.assertRaises(Exception):
            stop_container(self.deployment)

        self.deployment.refresh_from_db()
        self.assertEqual(self.deployment.status, Deployment.Status.FAILED)

    @patch('projects.services.get_docker_client')
    def test_restart_container_failure(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = Exception("Docker restart error")

        with self.assertRaises(Exception):
            restart_container(self.deployment)

        self.deployment.refresh_from_db()
        self.assertEqual(self.deployment.status, Deployment.Status.FAILED)

    @patch('projects.services.get_docker_client')
    def test_remove_container_failure(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = Exception("Docker remove error")

        with self.assertRaises(Exception):
            remove_container(self.deployment)

        self.deployment.refresh_from_db()
        # status shouldn't change to REMOVED if it fails
        self.assertNotEqual(self.deployment.status, Deployment.Status.REMOVED)

    @patch('projects.services.get_docker_client')
    def test_get_deployment_logs_container_not_found(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = docker.errors.NotFound("Container not found")

        logs = get_deployment_logs(self.deployment)
        self.assertEqual(logs, "")
