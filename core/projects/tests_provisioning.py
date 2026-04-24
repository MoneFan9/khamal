from django.test import TestCase
from unittest.mock import patch, MagicMock
from .models import Project
from .services import auto_provision_from_plan, provision_database
from .nixpacks import NixpacksPlan
from django.contrib.auth import get_user_model
import docker

User = get_user_model()

class ProvisioningTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser_prov", password="password")
        self.project = Project.objects.create(name="ProvProject", owner=self.user)

    @patch('projects.services.get_docker_client')
    @patch('projects.services.ensure_project_network')
    @patch('projects.services._wait_for_healthy')
    def test_provision_postgres(self, mock_wait, mock_ensure_net, mock_get_client):
        mock_ensure_net.return_value = "net_123"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")

        mock_net = MagicMock()
        mock_net.name = "khamal-project-net"
        mock_client.networks.get.return_value = mock_net

        provision_database(self.project, "postgres")

        mock_client.containers.run.assert_called_once()
        args, kwargs = mock_client.containers.run.call_args
        self.assertEqual(args[0], "postgres:16")
        self.assertEqual(kwargs['name'], f"khamal-db-postgres-{self.project.id}")
        self.assertEqual(kwargs['network'], "khamal-project-net")
        self.assertIn("POSTGRES_PASSWORD", kwargs['environment'])
        self.assertIn(f"khamal-data-postgres-{self.project.id}", kwargs['volumes'])
        mock_wait.assert_called_once()

    @patch('projects.services.get_docker_client')
    @patch('projects.services.ensure_project_network')
    @patch('projects.services._wait_for_healthy')
    def test_provision_redis(self, mock_wait, mock_ensure_net, mock_get_client):
        mock_ensure_net.return_value = "net_123"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")

        mock_net = MagicMock()
        mock_net.name = "khamal-project-net"
        mock_client.networks.get.return_value = mock_net

        provision_database(self.project, "redis")

        mock_client.containers.run.assert_called_once()
        args, kwargs = mock_client.containers.run.call_args
        self.assertEqual(args[0], "redis:7-alpine")
        self.assertEqual(kwargs['name'], f"khamal-db-redis-{self.project.id}")

    @patch('projects.services.provision_database')
    def test_auto_provision_from_plan(self, mock_provision):
        # Precise match
        plan = NixpacksPlan(
            packages=["python311", "postgresql"],
            libraries=["libpq"]
        )

        auto_provision_from_plan(self.project, plan)

        mock_provision.assert_called_once_with(self.project, "postgres")

    @patch('projects.services.provision_database')
    def test_auto_provision_redis_from_plan(self, mock_provision):
        # Redis in libraries (bug fix test)
        plan = NixpacksPlan(
            libraries=["redis"]
        )

        auto_provision_from_plan(self.project, plan)

        mock_provision.assert_called_once_with(self.project, "redis")

    @patch('projects.services.provision_database')
    def test_auto_provision_both_from_plan(self, mock_provision):
        plan = NixpacksPlan(
            packages=["postgresql", "redis"]
        )

        auto_provision_from_plan(self.project, plan)

        self.assertEqual(mock_provision.call_count, 2)

    @patch('projects.services.get_docker_client')
    @patch('projects.services.ensure_project_network')
    def test_provision_database_race_condition(self, mock_ensure_net, mock_get_client):
        mock_ensure_net.return_value = "net_123"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_net = MagicMock()
        mock_net.name = "khamal-project-net"
        mock_client.networks.get.return_value = mock_net

        # First call to get() fails, second (after conflict) succeeds
        mock_client.containers.get.side_effect = [
            docker.errors.NotFound("Not found"),
            MagicMock()
        ]

        # Mock 409 Conflict
        response = MagicMock()
        response.status_code = 409
        mock_client.containers.run.side_effect = docker.errors.APIError("Conflict", response=response)

        provision_database(self.project, "postgres")

        # Should have called get() twice
        self.assertEqual(mock_client.containers.get.call_count, 2)
