import pytest
from unittest.mock import patch, MagicMock
from projects.services import (
    start_container, stop_container, restart_container, remove_container,
    _get_deployment_volumes, get_deployment_logs, get_routing_labels, ensure_global_proxy,
    ensure_project_network, delete_project_network, provision_database
)
from projects.models import Project, Deployment
from django.contrib.auth import get_user_model
import docker

User = get_user_model()

@pytest.fixture
def test_user(db):
    return User.objects.create_user(username="testuser", password="password")

@pytest.fixture
def project(db, test_user):
    return Project.objects.create(name="Test Project", domain="example.com", owner=test_user)

@pytest.fixture
def deployment(db, project):
    return Deployment.objects.create(project=project, container_id="fake_id", container_port=80)

@pytest.mark.django_db
class TestProjectsServicesExtended:

    @patch("projects.services.logger")
    def test_start_container_no_id(self, mock_logger, deployment):
        deployment.container_id = None
        start_container(deployment)
        mock_logger.error.assert_called_with(f"Cannot start deployment {deployment.id}: no container_id")

    def test_stop_container_no_id(self, deployment):
        deployment.container_id = None
        stop_container(deployment)

    def test_restart_container_no_id(self, deployment):
        deployment.container_id = None
        restart_container(deployment)

    def test_remove_container_no_id(self, deployment):
        deployment.container_id = None
        remove_container(deployment)

    @patch("projects.services.logger")
    def test_get_deployment_volumes_no_localsource(self, mock_logger, deployment):
        deployment.hot_reload = True
        volumes = _get_deployment_volumes(deployment)
        assert volumes == {}
        mock_logger.warning.assert_called_with(
            f"Hot-Reload enabled for deployment {deployment.id} but no LocalSource found for project {deployment.project.id}"
        )

    def test_get_deployment_logs_no_id(self, deployment):
        deployment.container_id = None
        logs = get_deployment_logs(deployment)
        assert logs == ""

    @patch("projects.services.get_docker_client")
    def test_get_deployment_logs_not_found(self, mock_docker_client, deployment):
        mock_client = MagicMock()
        mock_docker_client.return_value = mock_client
        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")

        logs = get_deployment_logs(deployment)
        assert logs == ""

    def test_get_routing_labels_no_domain(self, project, deployment):
        project.domain = ""
        labels = get_routing_labels(deployment)
        assert labels == {"khamal.managed": "true"}

    @patch("projects.services.get_docker_client")
    def test_ensure_global_proxy_ssl_enabled(self, mock_docker_client, settings):
        mock_client = MagicMock()
        mock_docker_client.return_value = mock_client
        mock_client.networks.get.side_effect = docker.errors.NotFound("Not found")
        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")

        settings.KHAMAL_SSL_ENABLED = True
        settings.KHAMAL_ACME_EMAIL = "test@example.com"
        settings.KHAMAL_ACME_STORAGE = "/letsencrypt/acme.json"
        settings.KHAMAL_ACME_CA_SERVER = "https://acme-staging-v02.api.letsencrypt.org/directory"

        ensure_global_proxy()

        args, kwargs = mock_client.containers.run.call_args
        command = kwargs.get('command')
        assert "--certificatesresolvers.le.acme.email=test@example.com" in command
        assert "khamal-letsencrypt" in kwargs.get('volumes')

    def test_get_routing_labels_ssl_enabled(self, deployment, settings):
        settings.KHAMAL_SSL_ENABLED = True
        labels = get_routing_labels(deployment)
        router_name = f"khamal-router-{deployment.id}"
        assert labels[f"traefik.http.routers.{router_name}.entrypoints"] == "websecure"
        assert labels[f"traefik.http.routers.{router_name}.tls"] == "true"

    @patch("projects.services.get_docker_client")
    def test_ensure_project_network_recreate(self, mock_docker_client, project):
        mock_client = MagicMock()
        mock_docker_client.return_value = mock_client

        project.network_id = "old_network_id"
        project.save()
        mock_client.networks.get.side_effect = docker.errors.NotFound("Not found")

        mock_network = MagicMock()
        mock_network.id = "new_network_id"
        mock_client.networks.list.return_value = []
        mock_client.networks.create.return_value = mock_network

        network_id = ensure_project_network(project)
        assert network_id == "new_network_id"
        project.refresh_from_db()
        assert project.network_id == "new_network_id"

    @patch("projects.services.get_docker_client")
    def test_delete_project_network_no_id(self, mock_docker_client, project):
        project.network_id = None
        project.save()
        delete_project_network(project)
        mock_docker_client.assert_not_called()

    @patch("projects.services.get_docker_client")
    def test_start_container_exception(self, mock_docker_client, deployment):
        mock_client = MagicMock()
        mock_docker_client.return_value = mock_client
        mock_client.containers.get.side_effect = Exception("Docker Error")

        with pytest.raises(Exception):
            start_container(deployment)
        deployment.refresh_from_db()
        assert deployment.status == Deployment.Status.FAILED

    @patch("projects.services.get_docker_client")
    def test_stop_container_exception(self, mock_docker_client, deployment):
        mock_client = MagicMock()
        mock_docker_client.return_value = mock_client
        mock_client.containers.get.side_effect = Exception("Docker Error")

        with pytest.raises(Exception):
            stop_container(deployment)
        deployment.refresh_from_db()
        assert deployment.status == Deployment.Status.FAILED

    @patch("projects.services.get_docker_client")
    def test_restart_container_exception(self, mock_docker_client, deployment):
        mock_client = MagicMock()
        mock_docker_client.return_value = mock_client
        mock_client.containers.get.side_effect = Exception("Docker Error")

        with pytest.raises(Exception):
            restart_container(deployment)
        deployment.refresh_from_db()
        assert deployment.status == Deployment.Status.FAILED

    @patch("projects.services.ensure_project_network")
    @patch("projects.services.get_docker_client")
    def test_provision_database_already_running(self, mock_docker_client, mock_ensure_network, project):
        mock_client = MagicMock()
        mock_docker_client.return_value = mock_client
        mock_ensure_network.return_value = "fake_net_id"

        mock_container = MagicMock()
        mock_container.status = "running"
        mock_client.containers.get.return_value = mock_container

        container = provision_database(project, "postgres")
        assert container == mock_container
        mock_container.start.assert_not_called()

    @patch("projects.services.ensure_project_network")
    @patch("projects.services.get_docker_client")
    @patch("projects.services._wait_for_healthy")
    def test_provision_database_race_condition(self, mock_wait, mock_docker_client, mock_ensure_network, project):
        mock_client = MagicMock()
        mock_docker_client.return_value = mock_client
        mock_ensure_network.return_value = "fake_net_id"

        error_response = MagicMock()
        error_response.status_code = 409
        mock_client.containers.run.side_effect = docker.errors.APIError("Conflict", response=error_response)

        mock_container = MagicMock()
        mock_client.containers.get.side_effect = [docker.errors.NotFound("Not found"), mock_container]

        container = provision_database(project, "postgres")
        assert container == mock_container
