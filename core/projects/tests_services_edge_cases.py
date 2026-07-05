from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from projects.models import Project, Deployment
from projects.services import (
    delete_project_network, start_container, stop_container,
    restart_container, get_routing_labels, _get_deployment_volumes,
    create_deployment_container, provision_database, ensure_project_network,
    remove_container
)
import docker
from django.conf import settings

class ProjectsServicesEdgeCasesTests(TestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser")
        self.project = Project.objects.create(name="Test Project", domain="test.local", owner=self.user)
        self.deployment = Deployment.objects.create(
            project=self.project,
            container_port=8000
        )

    @patch("projects.services.get_docker_client")
    def test_delete_project_network_exception(self, mock_get_client):
        self.project.network_id = "test-net-id"
        self.project.save()

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.networks.get.side_effect = Exception("Network delete failed")

        delete_project_network(self.project)

        self.project.refresh_from_db()
        self.assertIsNone(self.project.network_id)

    @patch("projects.services.get_docker_client")
    def test_start_container_exception(self, mock_get_client):
        self.deployment.container_id = "test-cont-id"
        self.deployment.save()

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = Exception("Start failed")

        with self.assertRaises(Exception):
            start_container(self.deployment)

        self.deployment.refresh_from_db()
        self.assertEqual(self.deployment.status, Deployment.Status.FAILED)

    @patch("projects.services.get_docker_client")
    def test_stop_container_exception(self, mock_get_client):
        self.deployment.container_id = "test-cont-id"
        self.deployment.save()

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = Exception("Stop failed")

        with self.assertRaises(Exception):
            stop_container(self.deployment)

        self.deployment.refresh_from_db()
        self.assertEqual(self.deployment.status, Deployment.Status.FAILED)

    @patch("projects.services.get_docker_client")
    def test_restart_container_exception(self, mock_get_client):
        self.deployment.container_id = "test-cont-id"
        self.deployment.save()

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = Exception("Restart failed")

        with self.assertRaises(Exception):
            restart_container(self.deployment)

        self.deployment.refresh_from_db()
        self.assertEqual(self.deployment.status, Deployment.Status.FAILED)

    @override_settings(KHAMAL_SSL_ENABLED=True, KHAMAL_ACME_EMAIL="test@example.com")
    def test_get_routing_labels_ssl(self):
        labels = get_routing_labels(self.deployment)
        self.assertEqual(labels["traefik.http.routers.khamal-router-" + str(self.deployment.id) + ".entrypoints"], "websecure")
        self.assertEqual(labels["traefik.http.routers.khamal-router-" + str(self.deployment.id) + ".tls"], "true")

    def test_get_deployment_volumes_no_localsource(self):
        self.deployment.hot_reload = True
        self.deployment.save()

        volumes = _get_deployment_volumes(self.deployment)
        self.assertEqual(volumes, {})

    @patch("projects.services.ensure_global_proxy")
    @patch("projects.services.ensure_project_network")
    @patch("projects.services.get_docker_client")
    def test_create_deployment_container_exception(self, mock_get_client, mock_ensure_net, mock_ensure_proxy):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.networks.get.side_effect = Exception("Run failed")

        with self.assertRaises(Exception):
            create_deployment_container(self.deployment, "test-image")

        self.deployment.refresh_from_db()
        self.assertEqual(self.deployment.status, Deployment.Status.FAILED)

    @patch("projects.services.ensure_project_network")
    @patch("projects.services._wait_for_healthy")
    @patch("projects.services.get_docker_client")
    def test_provision_database_not_healthy(self, mock_get_client, mock_wait, mock_ensure_net):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")
        mock_wait.return_value = False

        # Should complete but log a warning (which we don't necessarily assert here but it covers the line)
        provision_database(self.project, "postgres")
        mock_wait.assert_called_once()

    @patch("projects.services.ensure_project_network")
    @patch("projects.services.get_docker_client")
    def test_provision_database_race_condition(self, mock_get_client, mock_ensure_net):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # First call to get() fails, second call succeeds
        mock_client.containers.get.side_effect = [
            docker.errors.NotFound("Not found"),
            MagicMock(status="running")
        ]

        # Mock 409 Conflict APIError
        response = MagicMock()
        response.status_code = 409
        mock_client.containers.run.side_effect = docker.errors.APIError("Conflict", response=response)

        provision_database(self.project, "postgres")
        self.assertEqual(mock_client.containers.get.call_count, 2)

    @patch("projects.services.ensure_project_network")
    @patch("projects.services.get_docker_client")
    def test_provision_database_exception(self, mock_get_client, mock_ensure_net):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")
        mock_client.containers.run.side_effect = Exception("Run failed")

        with self.assertRaises(Exception):
            provision_database(self.project, "postgres")

    @patch("projects.services.get_docker_client")
    def test_ensure_project_network_recreate(self, mock_get_client):
        self.project.network_id = "old-net"
        self.project.save()

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        # get() fails for the old network
        mock_client.networks.get.side_effect = docker.errors.NotFound("Not found")
        # list() returns empty
        mock_client.networks.list.return_value = []
        # create() succeeds
        mock_net = MagicMock(id="new-net")
        # Ensure mock_net.id is a string, not another mock
        mock_net.id = "new-net"
        mock_client.networks.create.return_value = mock_net

        net_id = ensure_project_network(self.project)

        self.assertEqual(net_id, "new-net")
        self.project.refresh_from_db()
        self.assertEqual(self.project.network_id, "new-net")

    @patch("projects.services.get_docker_client")
    def test_ensure_project_network_exception(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.networks.list.return_value = []
        mock_client.networks.create.side_effect = Exception("Create failed")

        with self.assertRaises(Exception):
            ensure_project_network(self.project)

        self.project.refresh_from_db()
        self.assertIsNone(self.project.network_id)

    @patch("projects.services.get_docker_client")
    def test_ensure_project_network_existing_list(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_net = MagicMock(id="existing-net")
        mock_net.id = "existing-net"
        # Simulate 409
        response = MagicMock(status_code=409)
        mock_client.networks.create.side_effect = docker.errors.APIError("Conflict", response=response)
        mock_client.networks.list.return_value = [mock_net]

        net_id = ensure_project_network(self.project)
        self.assertEqual(net_id, "existing-net")

    def test_delete_project_network_none(self):
        self.project.network_id = None
        self.project.save()
        # Should return early
        delete_project_network(self.project)

    def test_start_container_none(self):
        self.deployment.container_id = None
        self.deployment.save()
        start_container(self.deployment)

    def test_stop_container_none(self):
        self.deployment.container_id = None
        self.deployment.save()
        stop_container(self.deployment)

    def test_restart_container_none(self):
        self.deployment.container_id = None
        self.deployment.save()
        restart_container(self.deployment)

    def test_remove_container_none(self):
        self.deployment.container_id = None
        self.deployment.save()
        remove_container(self.deployment)

    @patch("projects.services.get_docker_client")
    def test_remove_container_success(self, mock_get_client):
        self.deployment.container_id = "test-id"
        self.deployment.save()

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container

        remove_container(self.deployment)

        mock_container.remove.assert_called_once()
        self.deployment.refresh_from_db()
        self.assertIsNone(self.deployment.container_id)
        self.assertEqual(self.deployment.status, Deployment.Status.REMOVED)

    @patch("projects.services.get_docker_client")
    def test_remove_container_failure(self, mock_get_client):
        self.deployment.container_id = "test-id"
        self.deployment.save()

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = Exception("Remove failed")

        with self.assertRaises(Exception):
            remove_container(self.deployment)

    @patch("projects.services.ensure_project_network")
    @patch("projects.services.get_docker_client")
    def test_provision_database_exists_not_running(self, mock_get_client, mock_ensure_net):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_container = MagicMock(status="exited")
        mock_client.containers.get.return_value = mock_container

        provision_database(self.project, "postgres")
        mock_container.start.assert_called_once()
