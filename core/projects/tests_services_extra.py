import pytest
import docker
from unittest.mock import patch, MagicMock, PropertyMock
from django.conf import settings
from django.contrib.auth import get_user_model
from projects.models import Project, Deployment
from projects.services import (
    ensure_global_proxy, delete_project_network,
    start_container, stop_container, restart_container,
    remove_container, provision_database,
    _wait_for_healthy, _get_deployment_volumes,
    get_deployment_logs, get_routing_labels,
    ensure_project_network
)

@pytest.mark.django_db
class TestServicesExtra:

    @patch("projects.services.get_docker_client")
    def test_ensure_global_proxy_ssl_enabled(self, mock_get_client):
        client = MagicMock()
        mock_get_client.return_value = client
        client.networks.get.side_effect = docker.errors.NotFound("Network not found")
        client.containers.get.side_effect = docker.errors.NotFound("Container not found")

        with patch.object(settings, "KHAMAL_SSL_ENABLED", True), \
             patch.object(settings, "KHAMAL_ACME_EMAIL", "test@test.com"), \
             patch.object(settings, "KHAMAL_ACME_STORAGE", "/tmp/acme.json"), \
             patch.object(settings, "KHAMAL_ACME_CA_SERVER", "https://acme.staging.com"):

            ensure_global_proxy()

            # Check if containers.run was called with SSL labels/commands
            args, kwargs = client.containers.run.call_args
            command = kwargs.get("command", [])
            assert "--certificatesresolvers.le.acme.email=test@test.com" in command
            assert "khamal-letsencrypt" in kwargs.get("volumes", {})

    @patch("projects.services.get_docker_client")
    def test_delete_project_network_error_handling(self, mock_get_client, project):
        client = MagicMock()
        mock_get_client.return_value = client
        project.network_id = "some-id"
        project.save()

        client.networks.get.side_effect = Exception("Docker error")

        # Should not raise exception but log it and clear network_id
        delete_project_network(project)

        project.refresh_from_db()
        assert project.network_id is None

    @patch("projects.services.get_docker_client")
    def test_start_container_failure(self, mock_get_client, deployment):
        client = MagicMock()
        mock_get_client.return_value = client
        deployment.container_id = "cont-id"
        deployment.save()

        client.containers.get.side_effect = Exception("Failed to start")

        with pytest.raises(Exception):
            start_container(deployment)

        deployment.refresh_from_db()
        assert deployment.status == Deployment.Status.FAILED

    @patch("projects.services.get_docker_client")
    def test_remove_container_force(self, mock_get_client, deployment):
        client = MagicMock()
        mock_get_client.return_value = client
        deployment.container_id = "cont-id"
        deployment.save()

        container = MagicMock()
        client.containers.get.return_value = container

        remove_container(deployment, force=True)

        container.remove.assert_called_with(force=True)
        deployment.refresh_from_db()
        assert deployment.container_id is None
        assert deployment.status == Deployment.Status.REMOVED

    @patch("projects.services.get_docker_client")
    def test_provision_database_race_condition(self, mock_get_client, project):
        client = MagicMock()
        mock_get_client.return_value = client

        # Mocking get_docker_client to return a client that has a network
        # This is to avoid ensure_project_network creating a real network or failing
        project.network_id = "test-net"
        project.save()

        # Mocking NotFound for the initial get
        client.containers.get.side_effect = docker.errors.NotFound("Not found")

        # Mocking 409 Conflict for run
        response = MagicMock()
        response.status_code = 409
        client.containers.run.side_effect = docker.errors.APIError("Conflict", response=response)

        # Second get should return the container
        existing_container = MagicMock()
        client.containers.get.side_effect = [docker.errors.NotFound("Not found"), existing_container]

        result = provision_database(project, "postgres")
        assert result == existing_container

    @patch("projects.services.get_docker_client")
    def test_provision_database_general_api_error(self, mock_get_client, project):
        client = MagicMock()
        mock_get_client.return_value = client
        project.network_id = "test-net"
        project.save()

        client.containers.get.side_effect = docker.errors.NotFound("Not found")

        response = MagicMock()
        response.status_code = 500
        client.containers.run.side_effect = docker.errors.APIError("Server error", response=response)

        with pytest.raises(docker.errors.APIError):
            provision_database(project, "postgres")

    def test_wait_for_healthy_success(self):
        container = MagicMock()
        container.attrs = {"State": {"Health": {"Status": "healthy"}}}
        assert _wait_for_healthy(container, timeout=1) is True

    def test_wait_for_healthy_running_no_healthcheck(self):
        container = MagicMock()
        container.attrs = {"State": {}}
        container.status = "running"
        assert _wait_for_healthy(container, timeout=1) is True

    def test_wait_for_healthy_exited(self):
        container = MagicMock()
        container.attrs = {"State": {}}
        container.status = "exited"
        assert _wait_for_healthy(container, timeout=1) is False

    @patch("projects.services.time.sleep")
    @patch("projects.services.time.monotonic")
    def test_wait_for_healthy_timeout(self, mock_monotonic, mock_sleep):
        container = MagicMock()
        container.attrs = {"State": {"Health": {"Status": "starting"}}}
        container.status = "starting"

        # Mocking time to simulate a timeout
        mock_monotonic.side_effect = [0, 10, 70]

        assert _wait_for_healthy(container, timeout=60) is False

    @patch("projects.services.get_docker_client")
    def test_stop_container_failure(self, mock_get_client, deployment):
        client = MagicMock()
        mock_get_client.return_value = client
        deployment.container_id = "cont-id"
        deployment.save()
        client.containers.get.side_effect = Exception("Stop failed")
        with pytest.raises(Exception):
            stop_container(deployment)
        deployment.refresh_from_db()
        assert deployment.status == Deployment.Status.FAILED

    @patch("projects.services.get_docker_client")
    def test_restart_container_failure(self, mock_get_client, deployment):
        client = MagicMock()
        mock_get_client.return_value = client
        deployment.container_id = "cont-id"
        deployment.save()
        client.containers.get.side_effect = Exception("Restart failed")
        with pytest.raises(Exception):
            restart_container(deployment)
        deployment.refresh_from_db()
        assert deployment.status == Deployment.Status.FAILED

    @patch("projects.services.get_docker_client")
    def test_remove_container_failure(self, mock_get_client, deployment):
        client = MagicMock()
        mock_get_client.return_value = client
        deployment.container_id = "cont-id"
        deployment.save()
        client.containers.get.side_effect = Exception("Remove failed")
        with pytest.raises(Exception):
            remove_container(deployment)

    def test_get_deployment_volumes_missing_localsource(self, deployment):
        deployment.hot_reload = True
        volumes = _get_deployment_volumes(deployment)
        assert volumes == {}

    @patch("projects.services.get_docker_client")
    def test_provision_database_unhealthy(self, mock_get_client, project):
        client = MagicMock()
        mock_get_client.return_value = client
        project.network_id = "test-net"
        project.save()
        client.containers.get.side_effect = docker.errors.NotFound("Not found")
        container = MagicMock()
        client.containers.run.return_value = container

        with patch("projects.services._wait_for_healthy", return_value=False):
            provision_database(project, "postgres")
            # Should just log warning, not raise exception

    def test_get_deployment_logs_container_not_found(self, deployment):
        deployment.container_id = "non-existent"
        with patch("projects.services.get_docker_client") as mock_get_client:
            client = MagicMock()
            mock_get_client.return_value = client
            client.containers.get.side_effect = docker.errors.NotFound("Not found")
            logs = get_deployment_logs(deployment)
            assert logs == ""

    def test_get_deployment_logs_general_failure(self, deployment):
        deployment.container_id = "cont-id"
        with patch("projects.services.get_docker_client") as mock_get_client:
            client = MagicMock()
            mock_get_client.return_value = client
            client.containers.get.side_effect = Exception("General failure")
            logs = get_deployment_logs(deployment)
            assert logs == ""

    @patch("projects.services.get_docker_client")
    def test_provision_database_already_exists_stopped(self, mock_get_client, project):
        client = MagicMock()
        mock_get_client.return_value = client
        project.network_id = "test-net"
        project.save()

        container = MagicMock()
        container.status = "exited"
        client.containers.get.return_value = container

        provision_database(project, "postgres")
        container.start.assert_called_once()

    @patch("projects.services.get_docker_client")
    def test_provision_database_general_exception(self, mock_get_client, project):
        client = MagicMock()
        mock_get_client.return_value = client
        project.network_id = "test-net"
        project.save()

        client.containers.get.side_effect = Exception("Unexpected error")
        with pytest.raises(Exception, match="Unexpected error"):
            provision_database(project, "postgres")

    @patch("projects.services.get_docker_client")
    def test_provision_database_run_general_exception(self, mock_get_client, project):
        client = MagicMock()
        mock_get_client.return_value = client
        project.network_id = "test-net"
        project.save()

        client.containers.get.side_effect = docker.errors.NotFound("Not found")
        client.containers.run.side_effect = Exception("Run failed")

        with pytest.raises(Exception, match="Run failed"):
            provision_database(project, "postgres")

    @patch("projects.services.get_docker_client")
    def test_stop_container_no_id(self, mock_get_client, deployment):
        deployment.container_id = None
        deployment.save()
        stop_container(deployment)

    @patch("projects.services.get_docker_client")
    def test_restart_container_no_id(self, mock_get_client, deployment):
        deployment.container_id = None
        deployment.save()
        restart_container(deployment)

    @patch("projects.services.get_docker_client")
    def test_remove_container_no_id(self, mock_get_client, deployment):
        deployment.container_id = None
        deployment.save()
        remove_container(deployment)

    def test_delete_project_network_no_id(self, project):
        project.network_id = None
        project.save()
        delete_project_network(project)

    def test_get_routing_labels_ssl(self, deployment):
        deployment.project.domain = "test.com"
        deployment.container_port = 8080
        with patch.object(settings, "KHAMAL_SSL_ENABLED", True):
            labels = get_routing_labels(deployment)
            assert labels[f"traefik.http.routers.khamal-router-{deployment.id}.tls"] == "true"
            assert labels[f"traefik.http.routers.khamal-router-{deployment.id}.entrypoints"] == "websecure"

    @patch("projects.services.get_docker_client")
    def test_ensure_project_network_existing_name(self, mock_get_client, project):
        client = MagicMock()
        mock_get_client.return_value = client

        existing_network = MagicMock()
        type(existing_network).id = PropertyMock(return_value="existing-id")
        client.networks.list.return_value = [existing_network]

        net_id = ensure_project_network(project)
        assert net_id == "existing-id"
        project.refresh_from_db()
        assert project.network_id == "existing-id"

    @patch("projects.services.get_docker_client")
    def test_start_container_no_id(self, mock_get_client, deployment):
        deployment.container_id = None
        deployment.save()
        start_container(deployment)
        # Should log error and return

    @patch("projects.services.get_docker_client")
    def test_ensure_project_network_recreate(self, mock_get_client, project):
        client = MagicMock()
        mock_get_client.return_value = client
        project.network_id = "old-id"
        project.save()

        # Mock network not found
        client.networks.get.side_effect = Exception("Not found")

        # Mock list to return empty
        client.networks.list.return_value = []

        # Mock creation of new network
        new_network = MagicMock()
        new_network.id = "new-id"
        # We need to ensure new_network.id is a string, not a MagicMock
        type(new_network).id = PropertyMock(return_value="new-id")
        client.networks.create.return_value = new_network

        net_id = ensure_project_network(project)
        assert net_id == "new-id"
        project.refresh_from_db()
        assert project.network_id == "new-id"

@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(username="testuser", password="password")

@pytest.fixture
def project(db, user):
    return Project.objects.create(name="Test Project", owner=user)

@pytest.fixture
def deployment(project):
    return Deployment.objects.create(project=project)
