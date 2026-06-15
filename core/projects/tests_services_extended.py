import pytest
import docker
from unittest.mock import patch, MagicMock
from django.conf import settings
from projects.models import Project, Deployment
from local.models import LocalSource
from projects.services import (
    ensure_project_network, delete_project_network, start_container,
    stop_container, restart_container, remove_container, get_routing_labels,
    _get_deployment_volumes, provision_database, _wait_for_healthy, get_deployment_logs
)
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestServicesExtended:

    @patch("projects.services.get_docker_client")
    def test_ensure_project_network_recreate(self, mock_get_client):
        user = User.objects.create(username="testuser")
        project = Project.objects.create(name="testproj", owner=user, network_id="old-id")

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.networks.get.side_effect = Exception("Not found")
        mock_client.networks.list.return_value = []
        mock_client.networks.create.return_value = MagicMock(id="new-id")

        network_id = ensure_project_network(project)
        assert network_id == "new-id"
        project.refresh_from_db()
        assert project.network_id == "new-id"

    @patch("projects.services.get_docker_client")
    def test_ensure_project_network_exists_by_name(self, mock_get_client):
        user = User.objects.create(username="testuser_byname")
        project = Project.objects.create(name="testproj_byname", owner=user)

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_network = MagicMock(id="existing-id")
        mock_client.networks.list.return_value = [mock_network]

        network_id = ensure_project_network(project)
        assert network_id == "existing-id"

    @patch("projects.services.get_docker_client")
    def test_container_lifecycle_exceptions(self, mock_get_client):
        user = User.objects.create(username="testuser_lifecycle")
        project = Project.objects.create(name="testproj_lifecycle", owner=user)
        deployment = Deployment.objects.create(project=project, container_id="cont-id")

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = Exception("Docker error")

        with pytest.raises(Exception):
            start_container(deployment)
        assert deployment.status == Deployment.Status.FAILED

        with pytest.raises(Exception):
            stop_container(deployment)
        assert deployment.status == Deployment.Status.FAILED

        with pytest.raises(Exception):
            restart_container(deployment)
        assert deployment.status == Deployment.Status.FAILED

        with pytest.raises(Exception):
            remove_container(deployment)

    def test_lifecycle_no_id(self):
        user = User.objects.create(username="testuser_noid")
        project = Project.objects.create(name="testproj_noid", owner=user)
        deployment = Deployment.objects.create(project=project, container_id=None)

        project_no_net = Project.objects.create(name="nonet", owner=user, network_id=None)

        # Test returns when no ID is present
        start_container(deployment)
        stop_container(deployment)
        restart_container(deployment)
        remove_container(deployment)
        delete_project_network(project_no_net)

    @patch("projects.services.get_docker_client")
    def test_delete_project_network_failure(self, mock_get_client):
        user = User.objects.create(username="testuser_netfail")
        project = Project.objects.create(name="testproj_netfail", owner=user, network_id="net-id")
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.networks.get.side_effect = Exception("Delete failed")

        delete_project_network(project)
        assert project.network_id is None

    def test_get_deployment_volumes_missing_localsource(self):
        user = User.objects.create(username="testuser")
        project = Project.objects.create(name="testproj", owner=user)
        deployment = Deployment.objects.create(project=project, hot_reload=True)

        volumes = _get_deployment_volumes(deployment)
        assert volumes == {}

    def test_get_deployment_volumes_hot_reload(self):
        user = User.objects.create(username="testuser_hr")
        project = Project.objects.create(name="testproj_hr", owner=user)
        LocalSource.objects.create(
            project=project,
            host_path="/tmp/host",
            container_path="/app"
        )
        deployment = Deployment.objects.create(project=project, hot_reload=True)

        volumes = _get_deployment_volumes(deployment)
        assert volumes == {"/tmp/host": {"bind": "/app", "mode": "rw"}}

    @patch("projects.services.time.sleep")
    def test_wait_for_healthy_exited(self, mock_sleep):
        container = MagicMock()
        container.attrs = {"State": {"Health": {"Status": "starting"}}}
        container.status = "exited"

        result = _wait_for_healthy(container, timeout=1)
        assert result is False

    @patch("projects.services.get_docker_client")
    @patch("projects.services.ensure_project_network")
    def test_provision_database_existing_running(self, mock_ensure_net, mock_get_client):
        user = User.objects.create(username="testuser_dbexist")
        project = Project.objects.create(name="testproj_dbexist", owner=user)
        mock_ensure_net.return_value = "net-id"

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_container = MagicMock()
        mock_container.status = "running"
        mock_client.containers.get.return_value = mock_container

        container = provision_database(project, "postgres")
        assert container == mock_container

    @patch("projects.services.get_docker_client")
    @patch("projects.services.ensure_project_network")
    def test_provision_database_existing_stopped(self, mock_ensure_net, mock_get_client):
        user = User.objects.create(username="testuser_dbstopped")
        project = Project.objects.create(name="testproj_dbstopped", owner=user)
        mock_ensure_net.return_value = "net-id"

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_container = MagicMock()
        mock_container.status = "stopped"
        mock_client.containers.get.return_value = mock_container

        container = provision_database(project, "postgres")
        assert container == mock_container
        mock_container.start.assert_called_once()

    @patch("projects.services.get_docker_client")
    @patch("projects.services.ensure_project_network")
    def test_provision_database_general_exception(self, mock_ensure_net, mock_get_client):
        user = User.objects.create(username="testuser_dbfail")
        project = Project.objects.create(name="testproj_dbfail", owner=user)
        mock_ensure_net.return_value = "net-id"

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = Exception("General error")

        with pytest.raises(Exception) as excinfo:
            provision_database(project, "postgres")
        assert "General error" in str(excinfo.value)

    @patch("projects.services.get_docker_client")
    @patch("projects.services.ensure_project_network")
    @patch("projects.services._wait_for_healthy")
    def test_provision_database_not_healthy(self, mock_wait, mock_ensure_net, mock_get_client):
        user = User.objects.create(username="testuser_dbunhealthy")
        project = Project.objects.create(name="testproj_dbunhealthy", owner=user)
        mock_ensure_net.return_value = "net-id"
        mock_wait.return_value = False

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")
        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container

        container = provision_database(project, "postgres")
        assert container == mock_container

    @patch("projects.services.get_docker_client")
    @patch("projects.services.ensure_project_network")
    def test_provision_database_race_condition(self, mock_ensure_net, mock_get_client):
        user = User.objects.create(username="testuser_race")
        project = Project.objects.create(name="testproj_race", owner=user)
        mock_ensure_net.return_value = "net-id"

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Simulate race condition (409 Conflict)
        response = MagicMock()
        response.status_code = 409
        mock_client.containers.run.side_effect = docker.errors.APIError("Conflict", response=response)
        mock_client.containers.get.side_effect = [docker.errors.NotFound("Not found"), MagicMock(id="existing-id")]

        container = provision_database(project, "postgres")
        assert container.id == "existing-id"

    @patch("projects.services.settings")
    def test_get_routing_labels_no_ssl(self, mock_settings):
        user = User.objects.create(username="testuser_nossl")
        project = Project.objects.create(name="testproj_nossl", owner=user, domain="example.com")
        deployment = Deployment.objects.create(project=project, container_port=80)

        mock_settings.KHAMAL_SSL_ENABLED = False
        labels = get_routing_labels(deployment)
        assert labels[f"traefik.http.routers.khamal-router-{deployment.id}.entrypoints"] == "web"

    @patch("projects.services.settings")
    def test_get_routing_labels_ssl(self, mock_settings):
        user = User.objects.create(username="testuser_ssl")
        project = Project.objects.create(name="testproj_ssl", owner=user, domain="example.com")
        deployment = Deployment.objects.create(project=project, container_port=8000)

        mock_settings.KHAMAL_SSL_ENABLED = True
        labels = get_routing_labels(deployment)
        assert labels[f"traefik.http.routers.khamal-router-{deployment.id}.tls"] == "true"

    @patch("projects.services.get_docker_client")
    def test_get_deployment_logs_not_found(self, mock_get_client):
        user = User.objects.create(username="testuser_logs")
        project = Project.objects.create(name="testproj_logs", owner=user)
        deployment = Deployment.objects.create(project=project, container_id="missing-id")

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")

        logs = get_deployment_logs(deployment)
        assert logs == ""

    @patch("projects.services.time.sleep")
    def test_wait_for_healthy_timeout(self, mock_sleep):
        container = MagicMock()
        container.attrs = {"State": {"Health": {"Status": "starting"}}}

        # Mock time to expire quickly
        with patch("projects.services.time.monotonic") as mock_time:
            mock_time.side_effect = [0, 100] # timeout is 60
            result = _wait_for_healthy(container)
            assert result is False
