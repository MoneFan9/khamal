import pytest
import docker
import time
from unittest.mock import patch, MagicMock
from django.conf import settings
from django.contrib.auth import get_user_model
from projects.models import Project, Deployment
from local.models import LocalSource
from projects.services import (
    ensure_project_network, delete_project_network, start_container,
    stop_container, restart_container, remove_container, get_routing_labels,
    _get_deployment_volumes, provision_database, _wait_for_healthy,
    get_deployment_logs
)

User = get_user_model()

@pytest.fixture
def test_user(db):
    return User.objects.create_user(username="testuser", password="password")

@pytest.mark.django_db
class TestServicesExtended:

    @patch("projects.services.get_docker_client")
    def test_ensure_project_network_recreate(self, mock_get_client, test_user):
        client = MagicMock()
        mock_get_client.return_value = client
        project = Project.objects.create(name="Test Project", owner=test_user, network_id="old-net")

        # client.networks.get fails, so it should recreate
        client.networks.get.side_effect = Exception("Not found")
        client.networks.list.return_value = []
        new_net = MagicMock(id="new-net")
        client.networks.create.return_value = new_net

        net_id = ensure_project_network(project)
        assert net_id == "new-net"
        project.refresh_from_db()
        assert project.network_id == "new-net"

    @patch("projects.services.get_docker_client")
    def test_ensure_project_network_exists_by_name(self, mock_get_client, test_user):
        project = Project.objects.create(name="Test Project", owner=test_user)
        client = MagicMock()
        mock_get_client.return_value = client
        existing_net = MagicMock(id="existing-net-id")
        client.networks.list.return_value = [existing_net]

        net_id = ensure_project_network(project)
        assert net_id == "existing-net-id"
        project.refresh_from_db()
        assert project.network_id == "existing-net-id"

    @patch("projects.services.get_docker_client")
    def test_ensure_project_network_failure(self, mock_get_client, test_user):
        client = MagicMock()
        mock_get_client.return_value = client
        project = Project.objects.create(name="Test Project", owner=test_user)
        client.networks.list.return_value = []
        client.networks.create.side_effect = Exception("Docker error")

        with pytest.raises(Exception):
            ensure_project_network(project)

    def test_lifecycle_no_id(self, test_user):
        project = Project.objects.create(name="Test Project", owner=test_user)
        deployment = Deployment.objects.create(project=project, container_id=None)

        # Should return early or handle gracefully
        start_container(deployment)
        stop_container(deployment)
        restart_container(deployment)
        remove_container(deployment)
        delete_project_network(project)

    @patch("projects.services.get_docker_client")
    def test_container_lifecycle_exceptions(self, mock_get_client, test_user):
        project = Project.objects.create(name="Test Project", owner=test_user)
        deployment = Deployment.objects.create(project=project, container_id="cont-123")

        client = MagicMock()
        mock_get_client.return_value = client
        client.containers.get.side_effect = Exception("Docker error")

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

    @patch("projects.services.get_docker_client")
    def test_delete_project_network_failure(self, mock_get_client, test_user):
        client = MagicMock()
        mock_get_client.return_value = client
        project = Project.objects.create(name="Test Project", owner=test_user, network_id="net-123")

        network = MagicMock()
        client.networks.get.return_value = network
        network.remove.side_effect = Exception("Removal failed")

        delete_project_network(project)
        project.refresh_from_db()
        assert project.network_id is None

    def test_get_routing_labels_ssl(self, test_user):
        project = Project.objects.create(name="Test Project", owner=test_user, domain="example.com")
        deployment = Deployment.objects.create(project=project, container_port=8000)

        with patch("projects.services.settings") as mock_settings:
            mock_settings.KHAMAL_SSL_ENABLED = True
            labels = get_routing_labels(deployment)
            assert labels[f"traefik.http.routers.khamal-router-{deployment.id}.tls"] == "true"

    def test_get_routing_labels_no_ssl(self, test_user):
        project = Project.objects.create(name="Test Project", owner=test_user, domain="example.com")
        deployment = Deployment.objects.create(project=project, container_port=80)

        with patch("projects.services.settings") as mock_settings:
            mock_settings.KHAMAL_SSL_ENABLED = False
            labels = get_routing_labels(deployment)
            assert labels[f"traefik.http.routers.khamal-router-{deployment.id}.entrypoints"] == "web"

    def test_get_deployment_volumes_hot_reload(self, test_user):
        project = Project.objects.create(name="Test Project", owner=test_user)
        LocalSource.objects.create(
            project=project,
            host_path="/tmp/host",
            container_path="/app"
        )
        deployment = Deployment.objects.create(project=project, hot_reload=True)

        volumes = _get_deployment_volumes(deployment)
        assert volumes == {"/tmp/host": {"bind": "/app", "mode": "rw"}}

    def test_get_deployment_volumes_missing_localsource(self, test_user):
        project = Project.objects.create(name="Test Project", owner=test_user)
        deployment = Deployment.objects.create(project=project, hot_reload=True)
        # No local_source created for project
        volumes = _get_deployment_volumes(deployment)
        assert volumes == {}

    def test_wait_for_healthy_exited(self):
        container = MagicMock()
        container.attrs = {"State": {"Health": {"Status": "starting"}}}
        container.status = "exited"

        with patch("projects.services.time.sleep"):
            result = _wait_for_healthy(container, timeout=1)
            assert result is False

    @patch("projects.services.time.sleep")
    def test_wait_for_healthy_timeout(self, mock_sleep):
        container = MagicMock()
        container.attrs = {"State": {"Health": {"Status": "starting"}}}
        container.status = "running"

        with patch("projects.services.time.monotonic") as mock_time:
            mock_time.side_effect = [0, 100]
            result = _wait_for_healthy(container)
            assert result is False

    @patch("projects.services.get_docker_client")
    @patch("projects.services.ensure_project_network")
    def test_provision_database_existing_running(self, mock_ensure_net, mock_get_client, test_user):
        project = Project.objects.create(name="Test Project", owner=test_user)
        client = MagicMock()
        mock_get_client.return_value = client
        mock_container = MagicMock()
        mock_container.status = "running"
        client.containers.get.return_value = mock_container

        container = provision_database(project, "postgres")
        assert container == mock_container

    @patch("projects.services.get_docker_client")
    @patch("projects.services.ensure_project_network")
    def test_provision_database_existing_stopped(self, mock_ensure_net, mock_get_client, test_user):
        project = Project.objects.create(name="Test Project", owner=test_user)
        client = MagicMock()
        mock_get_client.return_value = client
        mock_container = MagicMock()
        mock_container.status = "stopped"
        client.containers.get.return_value = mock_container

        container = provision_database(project, "postgres")
        assert container == mock_container
        mock_container.start.assert_called_once()

    @patch("projects.services.get_docker_client")
    @patch("projects.services.ensure_project_network")
    def test_provision_database_race_condition(self, mock_ensure_net, mock_get_client, test_user):
        client = MagicMock()
        mock_get_client.return_value = client
        project = Project.objects.create(name="Test Project", owner=test_user)

        response = MagicMock()
        response.status_code = 409
        mock_client = client
        mock_client.containers.run.side_effect = docker.errors.APIError("Conflict", response=response)
        mock_client.containers.get.side_effect = [docker.errors.NotFound("Not found"), MagicMock(id="existing-id")]

        container = provision_database(project, "postgres")
        assert container.id == "existing-id"

    @patch("projects.services.get_docker_client")
    @patch("projects.services.ensure_project_network")
    @patch("projects.services._wait_for_healthy")
    def test_provision_database_not_healthy(self, mock_wait, mock_ensure_net, mock_get_client, test_user):
        project = Project.objects.create(name="Test Project", owner=test_user)
        mock_wait.return_value = False
        client = MagicMock()
        mock_get_client.return_value = client
        client.containers.get.side_effect = docker.errors.NotFound("Not found")
        mock_container = MagicMock()
        client.containers.run.return_value = mock_container

        container = provision_database(project, "postgres")
        assert container == mock_container

    @patch("projects.services.get_docker_client")
    @patch("projects.services.ensure_project_network")
    def test_provision_database_failure(self, mock_ensure_net, mock_get_client, test_user):
        client = MagicMock()
        mock_get_client.return_value = client
        project = Project.objects.create(name="Test Project", owner=test_user)
        client.containers.get.side_effect = docker.errors.NotFound("Not found")
        client.containers.run.side_effect = Exception("Critical failure")

        with pytest.raises(Exception):
            provision_database(project, "postgres")

    @patch("projects.services.get_docker_client")
    def test_get_deployment_logs_not_found(self, mock_get_client, test_user):
        project = Project.objects.create(name="Test Project", owner=test_user)
        deployment = Deployment.objects.create(project=project, container_id="missing-id")

        client = MagicMock()
        mock_get_client.return_value = client
        client.containers.get.side_effect = docker.errors.NotFound("Not found")

        logs = get_deployment_logs(deployment)
        assert logs == ""
