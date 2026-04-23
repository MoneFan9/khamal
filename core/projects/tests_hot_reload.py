from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from .models import Project, Deployment
from local.models import LocalSource
from .services import create_deployment_container

User = get_user_model()

class HotReloadTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser_hr", password="password")
        self.project = Project.objects.create(name="HRProject", owner=self.user)
        self.local_source = LocalSource.objects.create(
            project=self.project,
            host_path="/home/user/app",
            container_path="/app"
        )
        self.deployment = Deployment.objects.create(
            project=self.project,
            container_port=80,
            hot_reload=True
        )

    @patch('projects.services.get_docker_client')
    @patch('projects.services.ensure_global_proxy')
    @patch('projects.services.ensure_project_network')
    def test_create_deployment_container_with_hot_reload(self, mock_ensure_project_net, mock_ensure_proxy, mock_get_client):
        mock_ensure_project_net.return_value = "net_123"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_container = MagicMock()
        mock_container.id = "cont_hr_123"
        mock_client.containers.run.return_value = mock_container

        mock_proxy_net = MagicMock()
        mock_client.networks.get.return_value = mock_proxy_net

        create_deployment_container(self.deployment, "nginx:latest")

        # Verify that volumes were passed to containers.run
        mock_client.containers.run.assert_called_once()
        args, kwargs = mock_client.containers.run.call_args

        volumes = kwargs.get('volumes', {})
        self.assertIn("/home/user/app", volumes)
        self.assertEqual(volumes["/home/user/app"]["bind"], "/app")
        self.assertEqual(volumes["/home/user/app"]["mode"], "rw")

    @patch('projects.services.get_docker_client')
    @patch('projects.services.ensure_global_proxy')
    @patch('projects.services.ensure_project_network')
    def test_create_deployment_container_without_hot_reload(self, mock_ensure_project_net, mock_ensure_proxy, mock_get_client):
        self.deployment.hot_reload = False
        self.deployment.save()

        mock_ensure_project_net.return_value = "net_123"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_container = MagicMock()
        mock_container.id = "cont_no_hr_123"
        mock_client.containers.run.return_value = mock_container

        mock_proxy_net = MagicMock()
        mock_client.networks.get.return_value = mock_proxy_net

        create_deployment_container(self.deployment, "nginx:latest")

        mock_client.containers.run.assert_called_once()
        args, kwargs = mock_client.containers.run.call_args

        volumes = kwargs.get('volumes', {})
        self.assertEqual(volumes, {})
