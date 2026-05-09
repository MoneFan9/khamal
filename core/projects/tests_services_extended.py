from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
from projects.models import Project, Deployment
from projects.services import (
    ensure_project_network, delete_project_network, start_container,
    stop_container, restart_container, remove_container, get_routing_labels,
    provision_database
)
import docker

class ProjectsServicesExtendedTests(TestCase):

    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.project = Project.objects.create(name="Test Project", owner=self.user)
        self.deployment = Deployment.objects.create(
            project=self.project,
            container_id="old-container-id",
            status=Deployment.Status.PENDING
        )

    @patch("projects.services.get_docker_client")
    def test_ensure_project_network_exists_by_name(self, mock_get_client):
        mock_client = MagicMock()
        mock_network = MagicMock()
        mock_network.id = "existing-network-id"
        # ensure_project_network first checks project.network_id (None here)
        # then it checks by name
        mock_client.networks.list.return_value = [mock_network]
        mock_get_client.return_value = mock_client

        ensure_project_network(self.project)

        self.assertEqual(self.project.network_id, "existing-network-id")
        mock_client.networks.create.assert_not_called()

    @patch("projects.services.get_docker_client")
    def test_delete_project_network_no_id(self, mock_get_client):
        self.project.network_id = ""
        delete_project_network(self.project)
        mock_get_client.assert_not_called()

    @patch("projects.services.get_docker_client")
    def test_delete_project_network_failure(self, mock_get_client):
        self.project.network_id = "some-id"
        mock_client = MagicMock()
        mock_client.networks.get.side_effect = Exception("Delete failed")
        mock_get_client.return_value = mock_client

        delete_project_network(self.project)

        self.assertIsNone(self.project.network_id)

    def test_start_container_no_id(self):
        self.deployment.container_id = ""
        with patch("projects.services.logger") as mock_logger:
            start_container(self.deployment)
            mock_logger.error.assert_called()

    def test_stop_container_no_id(self):
        self.deployment.container_id = ""
        stop_container(self.deployment) # Should return early

    def test_restart_container_no_id(self):
        self.deployment.container_id = ""
        restart_container(self.deployment) # Should return early

    def test_remove_container_no_id(self):
        self.deployment.container_id = ""
        remove_container(self.deployment) # Should return early

    @patch("projects.services.get_docker_client")
    def test_remove_container_failure(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.containers.get.side_effect = Exception("Remove failed")
        mock_get_client.return_value = mock_client

        with self.assertRaises(Exception):
            remove_container(self.deployment)

    @override_settings(KHAMAL_SSL_ENABLED=True)
    def test_get_routing_labels_ssl(self):
        labels = get_routing_labels(self.deployment)
        # Based on implementation, router name includes deployment id
        router_name = f"khamal-router-{self.deployment.id}"
        self.assertIn(f"traefik.http.routers.{router_name}.tls", labels)
        self.assertEqual(labels[f"traefik.http.routers.{router_name}.tls"], "true")

    @patch("projects.services.get_docker_client")
    @patch("projects.services.ensure_project_network")
    def test_provision_database_already_running(self, mock_ensure, mock_get_client):
        mock_ensure.return_value = "net-id"
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_container.status = "running"
        mock_client.containers.get.return_value = mock_container
        mock_get_client.return_value = mock_client

        result = provision_database(self.project, "postgres")
        self.assertEqual(result, mock_container)
        mock_container.start.assert_not_called()

    @patch("projects.services.get_docker_client")
    @patch("projects.services.ensure_project_network")
    def test_provision_database_exists_but_stopped(self, mock_ensure, mock_get_client):
        mock_ensure.return_value = "net-id"
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_container.status = "exited"
        mock_client.containers.get.return_value = mock_container
        mock_get_client.return_value = mock_client

        result = provision_database(self.project, "postgres")
        self.assertEqual(result, mock_container)
        mock_container.start.assert_called_once()

    @patch("projects.services.get_docker_client")
    @patch("projects.services.ensure_project_network")
    @patch("projects.services._wait_for_healthy")
    def test_provision_database_not_healthy(self, mock_wait, mock_ensure, mock_get_client):
        mock_ensure.return_value = MagicMock(name="net-obj")
        mock_ensure.return_value.name = "net-name"
        mock_client = MagicMock()
        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")
        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container
        mock_get_client.return_value = mock_client
        mock_wait.return_value = False

        with patch("projects.services.logger") as mock_logger:
            provision_database(self.project, "postgres")
            mock_logger.warning.assert_called_with(f"Database container khamal-db-postgres-{self.project.id} did not become healthy in time.")

    @patch("projects.services.get_docker_client")
    @patch("projects.services.ensure_project_network")
    def test_provision_database_race_condition(self, mock_ensure, mock_get_client):
        mock_ensure.return_value = MagicMock(name="net-obj")
        mock_ensure.return_value.name = "net-name"
        mock_client = MagicMock()
        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")

        # Mock APIError with 409 status code
        response = MagicMock()
        response.status_code = 409
        error = docker.errors.APIError("Conflict", response=response)
        mock_client.containers.run.side_effect = error

        mock_existing_container = MagicMock()
        # Second call to get should return the existing one
        mock_client.containers.get.side_effect = [docker.errors.NotFound("Not found"), mock_existing_container]
        mock_get_client.return_value = mock_client

        result = provision_database(self.project, "postgres")
        self.assertEqual(result, mock_existing_container)

    @patch("projects.services.get_docker_client")
    @patch("projects.services.ensure_project_network")
    def test_provision_database_other_exception(self, mock_ensure, mock_get_client):
        mock_ensure.return_value = "net-id"
        mock_client = MagicMock()
        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")
        mock_client.containers.run.side_effect = Exception("General error")
        mock_get_client.return_value = mock_client

        with self.assertRaises(Exception):
            provision_database(self.project, "postgres")

    def test_get_deployment_volumes_hot_reload_no_source(self):
        from projects.services import _get_deployment_volumes
        self.deployment.hot_reload = True
        # No LocalSource created for project
        with patch("projects.services.logger") as mock_logger:
            volumes = _get_deployment_volumes(self.deployment)
            self.assertEqual(volumes, {})
            mock_logger.warning.assert_called()

    def test_get_deployment_volumes_hot_reload_with_source(self):
        from projects.services import _get_deployment_volumes
        from local.models import LocalSource
        self.deployment.hot_reload = True
        LocalSource.objects.create(
            project=self.project,
            host_path="/tmp/host",
            container_path="/app"
        )
        volumes = _get_deployment_volumes(self.deployment)
        self.assertEqual(volumes["/tmp/host"]["bind"], "/app")
