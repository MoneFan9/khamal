import pytest
from unittest.mock import patch, MagicMock
from django.conf import settings
from django.contrib.auth import get_user_model
from projects.models import Project, Deployment
from local.models import LocalSource
from projects.services import (
    ensure_project_network, delete_project_network, start_container,
    stop_container, restart_container, remove_container, get_routing_labels,
    _get_deployment_volumes, provision_database, _wait_for_healthy
)
import docker
import time

User = get_user_model()

@pytest.fixture
def test_user(db):
    return User.objects.create_user(username="testuser", password="password")

@pytest.mark.django_db
class TestProjectsServicesExtended:

    @patch("projects.services.get_docker_client")
    def test_ensure_project_network_recreate(self, mock_get_client, test_user):
        client = MagicMock()
        mock_get_client.return_value = client
        project = Project.objects.create(name="Test Project", owner=test_user, network_id="old-net")

        # client.networks.get fails, so it should recreate
        client.networks.get.side_effect = docker.errors.NotFound("Not found")
        new_net = MagicMock(id="new-net")
        client.networks.create.return_value = new_net

        net_id = ensure_project_network(project)
        assert net_id == "new-net"
        project.refresh_from_db()
        assert project.network_id == "new-net"

    @patch("projects.services.get_docker_client")
    def test_ensure_project_network_existing_name(self, mock_get_client, test_user):
        client = MagicMock()
        mock_get_client.return_value = client
        project = Project.objects.create(name="Test Project", owner=test_user)

        existing_net = MagicMock(id="existing-net-id")
        # Simulate 409 Conflict when creating
        response = MagicMock(status_code=409)
        client.networks.create.side_effect = docker.errors.APIError("Conflict", response=response)
        # First list (if any) or follow up list after 409
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
        client.networks.create.side_effect = Exception("Docker error")

        with pytest.raises(Exception):
            ensure_project_network(project)

    def test_delete_project_network_no_id(self, test_user):
        project = Project.objects.create(name="Test Project", owner=test_user)
        # Should return early
        delete_project_network(project)

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
        assert project.network_id is None # It sets to None even on failure in the catch block

    def test_start_container_no_id(self, test_user):
        project = Project.objects.create(name="Test Project", owner=test_user)
        deployment = Deployment.objects.create(project=project)
        # Should return early and log error
        start_container(deployment)

    @patch("projects.services.get_docker_client")
    def test_start_container_failure(self, mock_get_client, test_user):
        client = MagicMock()
        mock_get_client.return_value = client
        project = Project.objects.create(name="Test Project", owner=test_user)
        deployment = Deployment.objects.create(project=project, container_id="cont-123")

        client.containers.get.side_effect = Exception("Start failed")

        with pytest.raises(Exception):
            start_container(deployment)
        deployment.refresh_from_db()
        assert deployment.status == Deployment.Status.FAILED

    def test_stop_container_no_id(self, test_user):
        project = Project.objects.create(name="Test Project", owner=test_user)
        deployment = Deployment.objects.create(project=project)
        # Should return early
        stop_container(deployment)

    @patch("projects.services.get_docker_client")
    def test_stop_container_failure(self, mock_get_client, test_user):
        client = MagicMock()
        mock_get_client.return_value = client
        project = Project.objects.create(name="Test Project", owner=test_user)
        deployment = Deployment.objects.create(project=project, container_id="cont-123")

        client.containers.get.side_effect = Exception("Stop failed")

        with pytest.raises(Exception):
            stop_container(deployment)
        deployment.refresh_from_db()
        assert deployment.status == Deployment.Status.FAILED

    def test_restart_container_no_id(self, test_user):
        project = Project.objects.create(name="Test Project", owner=test_user)
        deployment = Deployment.objects.create(project=project)
        # Should return early
        restart_container(deployment)

    @patch("projects.services.get_docker_client")
    def test_restart_container_failure(self, mock_get_client, test_user):
        client = MagicMock()
        mock_get_client.return_value = client
        project = Project.objects.create(name="Test Project", owner=test_user)
        deployment = Deployment.objects.create(project=project, container_id="cont-123")

        client.containers.get.side_effect = Exception("Restart failed")

        with pytest.raises(Exception):
            restart_container(deployment)
        deployment.refresh_from_db()
        assert deployment.status == Deployment.Status.FAILED

    def test_remove_container_no_id(self, test_user):
        project = Project.objects.create(name="Test Project", owner=test_user)
        deployment = Deployment.objects.create(project=project)
        # Should return early
        remove_container(deployment)

    @patch("projects.services.get_docker_client")
    def test_remove_container_failure(self, mock_get_client, test_user):
        client = MagicMock()
        mock_get_client.return_value = client
        project = Project.objects.create(name="Test Project", owner=test_user)
        deployment = Deployment.objects.create(project=project, container_id="cont-123")

        client.containers.get.side_effect = Exception("Remove failed")

        with pytest.raises(Exception):
            remove_container(deployment)

    def test_get_routing_labels_ssl(self, test_user):
        project = Project.objects.create(name="Test Project", owner=test_user, domain="example.com")
        deployment = Deployment.objects.create(project=project, container_port=8000)

        with patch.object(settings, "KHAMAL_SSL_ENABLED", True):
            labels = get_routing_labels(deployment)
            assert labels[f"traefik.http.routers.khamal-router-{deployment.id}.tls"] == "true"

    def test_get_deployment_volumes_hot_reload(self, test_user):
        project = Project.objects.create(name="Test Project", owner=test_user)
        local_source = LocalSource.objects.create(
            project=project,
            host_path="/tmp/host",
            container_path="/app"
        )
        deployment = Deployment.objects.create(project=project, hot_reload=True)

        volumes = _get_deployment_volumes(deployment)
        assert volumes == {"/tmp/host": {"bind": "/app", "mode": "rw"}}

    def test_get_deployment_volumes_no_localsource(self, test_user):
        project = Project.objects.create(name="Test Project", owner=test_user)
        deployment = Deployment.objects.create(project=project, hot_reload=True)
        # No local_source created for project
        volumes = _get_deployment_volumes(deployment)
        assert volumes == {}

    def test_wait_for_healthy_exited(self):
        container = MagicMock()
        container.attrs = {"State": {"Health": {"Status": "starting"}}}
        container.status = "exited"

        result = _wait_for_healthy(container)
        assert result is False

    @patch("projects.services.get_docker_client")
    @patch("projects.services.ensure_project_network")
    def test_provision_database_start_existing(self, mock_ensure_net, mock_get_client, test_user):
        client = MagicMock()
        mock_get_client.return_value = client
        project = Project.objects.create(name="Test Project", owner=test_user)

        db_container = MagicMock()
        db_container.status = "exited"
        client.containers.get.return_value = db_container

        provision_database(project, "postgres")
        db_container.start.assert_called_once()

    @patch("projects.services.get_docker_client")
    @patch("projects.services.ensure_project_network")
    def test_provision_database_race_condition(self, mock_ensure_net, mock_get_client, test_user):
        client = MagicMock()
        mock_get_client.return_value = client
        project = Project.objects.create(name="Test Project", owner=test_user)

        client.containers.get.side_effect = docker.errors.NotFound("Not found")

        # Mock APIError 409
        response = MagicMock()
        response.status_code = 409
        error = docker.errors.APIError("Conflict", response=response)
        client.containers.run.side_effect = error

        # Second get should return the container
        db_container = MagicMock()
        client.containers.get.side_effect = [docker.errors.NotFound("Not found"), db_container]

        res = provision_database(project, "postgres")
        assert res == db_container

    @patch("projects.services.time.sleep")
    def test_wait_for_healthy_timeout(self, mock_sleep):
        container = MagicMock()
        container.attrs = {"State": {"Health": {"Status": "starting"}}}

        # Mock time to expire quickly
        with patch("projects.services.time.monotonic") as mock_time:
            mock_time.side_effect = [0, 100] # timeout is 60
            result = _wait_for_healthy(container)
            assert result is False

    @patch("projects.services.get_docker_client")
    @patch("projects.services.ensure_project_network")
    @patch("projects.services._wait_for_healthy")
    def test_provision_database_unhealthy(self, mock_wait, mock_ensure_net, mock_get_client, test_user):
        client = MagicMock()
        mock_get_client.return_value = client
        mock_wait.return_value = False
        project = Project.objects.create(name="Test Project", owner=test_user)
        client.containers.get.side_effect = docker.errors.NotFound("Not found")

        db_container = MagicMock()
        client.containers.run.return_value = db_container

        provision_database(project, "postgres")
        # Should complete and log warning (warning is not easily assertable here without mocking logger)

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
