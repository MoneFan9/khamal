from django.test import TestCase, RequestFactory
from unittest.mock import patch, MagicMock
from projects.services import (
    ensure_project_network, start_container, stop_container,
    restart_container, remove_container, _get_deployment_volumes,
    provision_database, delete_project_network, get_routing_labels
)
from projects.models import Project, Deployment
from local.models import LocalSource
from projects.api_views import DeploymentListCreateAPIView
from django.contrib.auth import get_user_model
from django.conf import settings
import docker

User = get_user_model()

class ServicesExtendedTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        self.project = Project.objects.create(name="testproject", owner=self.user)
        self.deployment = Deployment.objects.create(project=self.project)

    @patch("projects.services.get_docker_client")
    def test_ensure_project_network_exists(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_network = MagicMock()
        mock_network.id = "existing_id"
        mock_client.networks.list.return_value = [mock_network]

        network_id = ensure_project_network(self.project)
        self.assertEqual(network_id, "existing_id")
        self.assertEqual(self.project.network_id, "existing_id")

    def test_delete_project_network_no_id(self):
        self.project.network_id = None
        # Should return early
        delete_project_network(self.project)

    def test_lifecycle_missing_container_id(self):
        # start_container
        with self.assertLogs("projects.services", level="ERROR") as cm:
            start_container(self.deployment)
            self.assertIn("no container_id", cm.output[0])

        # stop_container
        stop_container(self.deployment) # Should return early

        # restart_container
        restart_container(self.deployment) # Should return early

        # remove_container
        remove_container(self.deployment) # Should return early

    @patch("projects.services.get_docker_client")
    def test_remove_container_exception(self, mock_get_client):
        self.deployment.container_id = "cid"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_container = MagicMock()
        mock_container.remove.side_effect = Exception("Docker error")
        mock_client.containers.get.return_value = mock_container

        with self.assertRaises(Exception):
            remove_container(self.deployment)

    def test_get_routing_labels_ssl_enabled(self):
        with self.settings(KHAMAL_SSL_ENABLED=True):
            labels = get_routing_labels(self.deployment)
            self.assertEqual(labels[f"traefik.http.routers.khamal-router-{self.deployment.id}.tls"], "true")

    @patch("projects.services.logger")
    def test_get_deployment_volumes_no_local_source(self, mock_logger):
        self.deployment.hot_reload = True
        volumes = _get_deployment_volumes(self.deployment)
        self.assertEqual(volumes, {})
        mock_logger.warning.assert_called()

    @patch("projects.services.get_docker_client")
    def test_provision_database_existing_not_running(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_container = MagicMock()
        mock_container.status = "exited"
        mock_client.containers.get.return_value = mock_container

        mock_network = MagicMock()
        mock_network.id = "net_id"
        mock_client.networks.list.return_value = [mock_network]

        provision_database(self.project, "postgres")
        mock_container.start.assert_called_once()

    @patch("projects.services.get_docker_client")
    @patch("projects.services._wait_for_healthy")
    def test_provision_database_timeout(self, mock_wait, mock_get_client):
        mock_wait.return_value = False
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")

        mock_network = MagicMock()
        mock_network.id = "net_id"
        mock_client.networks.list.return_value = [mock_network]

        with self.assertLogs("projects.services", level="WARNING") as cm:
            provision_database(self.project, "postgres")
            self.assertIn("did not become healthy in time", cm.output[0])

    @patch("projects.services.get_docker_client")
    def test_provision_database_generic_exception(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")
        mock_client.containers.run.side_effect = Exception("Generic error")

        mock_network = MagicMock()
        mock_network.id = "net_id"
        mock_client.networks.list.return_value = [mock_network]

        with self.assertRaises(Exception):
            provision_database(self.project, "postgres")

class ApiViewsExtendedTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="testuser2")
        self.other_user = User.objects.create_user(username="otheruser")
        self.project = Project.objects.create(name="p1", owner=self.user)
        self.other_project = Project.objects.create(name="p2", owner=self.other_user)
        self.d1 = Deployment.objects.create(project=self.project)
        self.d2 = Deployment.objects.create(project=self.other_project)

    def test_deployment_list_queryset_filtering(self):
        view = DeploymentListCreateAPIView()
        request = self.factory.get('/api/deployments/')
        request.user = self.user
        view.request = request

        qs = view.get_queryset()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs[0], self.d1)
