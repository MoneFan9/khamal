from django.test import TestCase
from unittest.mock import patch, MagicMock
from .models import Project, Deployment
from .services import (
    ensure_project_network,
    delete_project_network,
    start_container,
    stop_container,
    restart_container,
    remove_container
)
from django.contrib.auth import get_user_model

User = get_user_model()

class NetworkServiceTest(TestCase):
    def setUp(self):
        # We need a user to own the project
        self.user = User.objects.create_user(username="testuser", password="password")
        # Ensure project name has no spaces for easier testing of network name
        self.project = Project.objects.create(name="TestProject", owner=self.user)

    @patch('projects.services.get_docker_client')
    def test_ensure_project_network_creates_new(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.networks.list.return_value = []

        mock_network = MagicMock()
        mock_network.id = "net_123"
        mock_client.networks.create.return_value = mock_network

        network_id = ensure_project_network(self.project)

        self.assertEqual(network_id, "net_123")
        self.project.refresh_from_db()
        self.assertEqual(self.project.network_id, "net_123")
        mock_client.networks.create.assert_called_once()
        args, kwargs = mock_client.networks.create.call_args
        self.assertIn("khamal-project-", args[0])
        self.assertEqual(kwargs['driver'], "bridge")

    @patch('projects.services.get_docker_client')
    def test_ensure_project_network_existing_id(self, mock_get_client):
        self.project.network_id = "existing_id"
        self.project.save()

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        network_id = ensure_project_network(self.project)

        self.assertEqual(network_id, "existing_id")
        mock_client.networks.get.assert_called_once_with("existing_id")
        mock_client.networks.create.assert_not_called()

    @patch('projects.services.get_docker_client')
    def test_delete_project_network(self, mock_get_client):
        self.project.network_id = "net_to_delete"
        self.project.save()

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_network = MagicMock()
        mock_client.networks.get.return_value = mock_network

        delete_project_network(self.project)

        mock_network.remove.assert_called_once()
        self.project.refresh_from_db()
        self.assertIsNone(self.project.network_id)

class ContainerServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser_container", password="password")
        self.project = Project.objects.create(name="TestProjectContainer", owner=self.user)
        self.deployment = Deployment.objects.create(
            project=self.project,
            container_id="cont_123",
            status=Deployment.Status.PENDING
        )

    @patch('projects.services.get_docker_client')
    def test_start_container(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container

        start_container(self.deployment)

        mock_container.start.assert_called_once()
        self.deployment.refresh_from_db()
        self.assertEqual(self.deployment.status, Deployment.Status.RUNNING)

    @patch('projects.services.get_docker_client')
    def test_stop_container(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container

        stop_container(self.deployment)

        mock_container.stop.assert_called_once()
        self.deployment.refresh_from_db()
        self.assertEqual(self.deployment.status, Deployment.Status.STOPPED)

    @patch('projects.services.get_docker_client')
    def test_restart_container(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container

        restart_container(self.deployment)

        mock_container.restart.assert_called_once()
        self.deployment.refresh_from_db()
        self.assertEqual(self.deployment.status, Deployment.Status.RUNNING)

    @patch('projects.services.get_docker_client')
    def test_remove_container(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container

        remove_container(self.deployment)

        mock_container.remove.assert_called_once()
        self.deployment.refresh_from_db()
        self.assertEqual(self.deployment.status, Deployment.Status.REMOVED)
        self.assertIsNone(self.deployment.container_id)
