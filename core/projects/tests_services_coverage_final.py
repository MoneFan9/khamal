import pytest
import docker
from unittest.mock import patch, MagicMock
from django.conf import settings
from projects.models import Deployment
from projects.services import (
    ensure_project_network, delete_project_network,
    start_container, stop_container, restart_container,
    remove_container, get_routing_labels, _get_deployment_volumes,
    provision_database, get_deployment_logs
)
from local.models import LocalSource

@pytest.mark.django_db
class TestServicesCoverageFinal:

    @patch("projects.services.get_docker_client")
    def test_ensure_project_network_already_exists(self, mock_get_client, project):
        client = MagicMock()
        mock_get_client.return_value = client

        network = MagicMock()
        network.id = "existing-net-id"
        # Simulate 409 Conflict
        response = MagicMock(status_code=409)
        client.networks.create.side_effect = docker.errors.APIError("Conflict", response=response)
        client.networks.list.return_value = [network]

        net_id = ensure_project_network(project)
        assert net_id == "existing-net-id"
        assert project.network_id == "existing-net-id"

    @patch("projects.services.get_docker_client")
    def test_delete_project_network_no_id(self, mock_get_client, project):
        project.network_id = None
        project.save()
        delete_project_network(project)
        # Should return early, mock_get_client not called
        assert not mock_get_client.called

    def test_start_container_no_id(self, deployment):
        deployment.container_id = None
        deployment.status = Deployment.Status.PENDING
        deployment.save()
        start_container(deployment)
        assert deployment.status == Deployment.Status.PENDING

    def test_stop_container_no_id(self, deployment):
        deployment.container_id = None
        deployment.status = Deployment.Status.PENDING
        deployment.save()
        stop_container(deployment)
        assert deployment.status == Deployment.Status.PENDING

    def test_restart_container_no_id(self, deployment):
        deployment.container_id = None
        deployment.status = Deployment.Status.PENDING
        deployment.save()
        restart_container(deployment)
        assert deployment.status == Deployment.Status.PENDING

    def test_remove_container_no_id(self, deployment):
        deployment.container_id = None
        deployment.status = Deployment.Status.PENDING
        deployment.save()
        remove_container(deployment)
        assert deployment.status == Deployment.Status.PENDING

    @patch("projects.services.get_docker_client")
    def test_remove_container_exception(self, mock_get_client, deployment):
        client = MagicMock()
        mock_get_client.return_value = client
        deployment.container_id = "some-id"
        deployment.save()

        client.containers.get.side_effect = Exception("Docker error")

        with pytest.raises(Exception):
            remove_container(deployment)

    def test_get_routing_labels_no_domain(self, deployment):
        # We need to bypass the save() method which auto-sets a domain
        from projects.models import Project
        Project.objects.filter(id=deployment.project.id).update(domain="")
        deployment.project.refresh_from_db()

        labels = get_routing_labels(deployment)
        assert labels == {"khamal.managed": "true"}

    def test_get_routing_labels_ssl_enabled(self, deployment):
        deployment.project.domain = "test.com"
        deployment.project.save()
        with patch.object(settings, "KHAMAL_SSL_ENABLED", True):
            labels = get_routing_labels(deployment)
            assert "traefik.http.routers.khamal-router-" + str(deployment.id) + ".tls" in labels

    def test_get_deployment_volumes_no_localsource(self, deployment):
        deployment.hot_reload = True
        deployment.save()
        # Ensure no LocalSource exists for this project
        LocalSource.objects.filter(project=deployment.project).delete()
        volumes = _get_deployment_volumes(deployment)
        assert volumes == {}

    @patch("projects.services.get_docker_client")
    @patch("projects.services._wait_for_healthy")
    def test_provision_database_unhealthy(self, mock_wait, mock_get_client, project):
        client = MagicMock()
        mock_get_client.return_value = client
        project.network_id = "test-net"
        project.save()

        client.containers.get.side_effect = docker.errors.NotFound("Not found")
        container = MagicMock()
        client.containers.run.return_value = container
        mock_wait.return_value = False

        result = provision_database(project, "postgres")
        assert result == container

    @patch("projects.services.get_docker_client")
    def test_provision_database_exception(self, mock_get_client, project):
        client = MagicMock()
        mock_get_client.return_value = client
        project.network_id = "test-net"
        project.save()

        client.containers.get.side_effect = Exception("General error")

        with pytest.raises(Exception):
            provision_database(project, "postgres")

    @patch("projects.services.get_docker_client")
    def test_provision_database_existing_stopped(self, mock_get_client, project):
        client = MagicMock()
        mock_get_client.return_value = client
        project.network_id = "test-net"
        project.save()

        container = MagicMock()
        container.status = "exited"
        client.containers.get.return_value = container

        result = provision_database(project, "postgres")
        assert result == container
        container.start.assert_called_once()

    def test_get_deployment_logs_no_id(self, deployment):
        deployment.container_id = None
        deployment.save()
        assert get_deployment_logs(deployment) == ""

    @patch("projects.services.get_docker_client")
    def test_get_deployment_logs_not_found(self, mock_get_client, deployment):
        client = MagicMock()
        mock_get_client.return_value = client
        deployment.container_id = "some-id"
        deployment.save()

        client.containers.get.side_effect = docker.errors.NotFound("Not found")
        assert get_deployment_logs(deployment) == ""

    @patch("projects.services.get_docker_client")
    def test_get_deployment_logs_exception(self, mock_get_client, deployment):
        client = MagicMock()
        mock_get_client.return_value = client
        deployment.container_id = "some-id"
        deployment.save()

        client.containers.get.side_effect = Exception("General error")
        assert get_deployment_logs(deployment) == ""

@pytest.fixture
def user(db):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(username="testuser_coverage", password="password")

@pytest.fixture
def project(db, user):
    from projects.models import Project
    return Project.objects.create(name="Test Project Coverage", owner=user)

@pytest.fixture
def deployment(project):
    return Deployment.objects.create(project=project)
