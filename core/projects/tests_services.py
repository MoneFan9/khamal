from django.test import TestCase
import docker
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

class TraefikServiceTest(TestCase):
    @patch('projects.services.get_docker_client')
    def test_ensure_global_proxy_creates_everything(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock network not found
        mock_client.networks.get.side_effect = docker.errors.NotFound("Network not found")
        # Mock container not found
        mock_client.containers.get.side_effect = docker.errors.NotFound("Container not found")

        from projects.services import ensure_global_proxy, PROXY_NETWORK_NAME, TRAEFIK_CONTAINER_NAME, TRAEFIK_IMAGE
        ensure_global_proxy()

        mock_client.networks.create.assert_called_once_with(
            PROXY_NETWORK_NAME,
            driver="bridge",
            labels={"khamal.managed": "true"}
        )

        mock_client.containers.run.assert_called_once()
        args, kwargs = mock_client.containers.run.call_args
        self.assertEqual(args[0], TRAEFIK_IMAGE)
        self.assertEqual(kwargs['name'], TRAEFIK_CONTAINER_NAME)
        self.assertTrue(kwargs['detach'])
        self.assertIn("--providers.docker=true", kwargs['command'])

class RoutingLabelsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser_routing", password="password")
        self.project = Project.objects.create(name="TestProjectRouting", owner=self.user, domain="example.com")
        self.deployment = Deployment.objects.create(
            project=self.project,
            container_port=8080
        )

    def test_get_routing_labels(self):
        from projects.services import get_routing_labels
        labels = get_routing_labels(self.deployment)

        self.assertEqual(labels["traefik.enable"], "true")
        self.assertEqual(labels[f"traefik.http.routers.khamal-router-{self.deployment.id}.rule"], "Host(`example.com`)")
        self.assertEqual(labels[f"traefik.http.services.khamal-service-{self.deployment.id}.loadbalancer.server.port"], "8080")
        self.assertEqual(labels["khamal.project.id"], str(self.project.id))

    def test_get_routing_labels_no_domain(self):
        # We need to bypass the auto-generation to test the "no domain" case in the service
        # or accept that now projects ALWAYS have a domain.
        # Given the requirements, a project should always have a domain.
        # So we update the test to reflect that.
        self.project.domain = ""
        # We use update_fields to bypass the save() logic if we really want to test empty domain
        Project.objects.filter(id=self.project.id).update(domain="")
        self.project.refresh_from_db()

        from projects.services import get_routing_labels
        labels = get_routing_labels(self.deployment)

        self.assertEqual(labels, {"khamal.managed": "true"})

class CreateDeploymentContainerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser_create", password="password")
        self.project = Project.objects.create(name="TestProjectCreate", owner=self.user, domain="test.com")
        self.deployment = Deployment.objects.create(
            project=self.project,
            container_port=3000
        )

    @patch('projects.services.get_docker_client')
    @patch('projects.services.ensure_global_proxy')
    @patch('projects.services.ensure_project_network')
    def test_create_deployment_container(self, mock_ensure_project_net, mock_ensure_proxy, mock_get_client):
        mock_ensure_project_net.return_value = "net_project_123"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_container = MagicMock()
        mock_container.id = "new_cont_123"
        mock_client.containers.run.return_value = mock_container

        mock_proxy_net = MagicMock()
        mock_client.networks.get.return_value = mock_proxy_net

        from projects.services import create_deployment_container
        create_deployment_container(self.deployment, "nginx:latest")

        mock_ensure_proxy.assert_called_once()
        mock_ensure_project_net.assert_called_once_with(self.project)

        mock_client.containers.run.assert_called_once()
        args, kwargs = mock_client.containers.run.call_args
        self.assertEqual(args[0], "nginx:latest")
        self.assertEqual(kwargs['network'], "net_project_123")
        self.assertEqual(kwargs['labels']['traefik.enable'], "true")

        mock_proxy_net.connect.assert_called_once_with(mock_container)

        self.deployment.refresh_from_db()
        self.assertEqual(self.deployment.container_id, "new_cont_123")
        self.assertEqual(self.deployment.status, Deployment.Status.RUNNING)
