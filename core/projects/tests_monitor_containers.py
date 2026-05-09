from io import StringIO
import sys
import time
from django.test import TestCase
from unittest.mock import patch, MagicMock
from projects.management.commands.monitor_containers import Command
from docker.errors import NotFound

class MonitorContainersTests(TestCase):
    def setUp(self):
        self.command = Command()

    def test_calculate_cpu_percent(self):
        """Test CPU percentage calculation with mock stats."""
        stats = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 1000000},
                "system_cpu_usage": 10000000,
                "online_cpus": 2
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 500000},
                "system_cpu_usage": 5000000
            }
        }
        # cpu_delta = 500000, system_delta = 5000000
        # (500000 / 5000000) * 2 * 100 = 20.0
        cpu_p = self.command.calculate_cpu_percent(stats)
        self.assertEqual(cpu_p, 20.0)

    def test_calculate_cpu_percent_zero_delta(self):
        stats = {
            "cpu_stats": {"cpu_usage": {"total_usage": 1000000}, "system_cpu_usage": 10000000},
            "precpu_stats": {"cpu_usage": {"total_usage": 1000000}, "system_cpu_usage": 10000000}
        }
        cpu_p = self.command.calculate_cpu_percent(stats)
        self.assertEqual(cpu_p, 0.0)

    def test_calculate_mem_usage(self):
        """Test Memory usage calculation with mock stats."""
        stats = {
            "memory_stats": {
                "usage": 1000 * 1024 * 1024,
                "limit": 2000 * 1024 * 1024,
                "stats": {"inactive_file": 200 * 1024 * 1024}
            }
        }
        # used = 1000 - 200 = 800
        # percent = (800 / 2000) * 100 = 40.0
        used, limit, percent = self.command.calculate_mem_usage(stats)
        self.assertEqual(used, 800 * 1024 * 1024)
        self.assertEqual(limit, 2000 * 1024 * 1024)
        self.assertEqual(percent, 40.0)

    def test_format_bytes(self):
        self.assertEqual(self.command.format_bytes(500), "500.00B")
        # The command uses while size > power, so 1024 is still B
        self.assertEqual(self.command.format_bytes(1024), "1024.00B")
        self.assertEqual(self.command.format_bytes(1025), "1.00KB")
        self.assertEqual(self.command.format_bytes(1024 * 1024 * 1.1), "1.10MB")

    @patch("projects.management.commands.monitor_containers.get_docker_client")
    @patch("projects.management.commands.monitor_containers.Deployment.objects.filter")
    @patch("projects.management.commands.monitor_containers.time.sleep")
    @patch("projects.management.commands.monitor_containers.sys.stdout.flush")
    def test_handle_no_deployments(self, mock_flush, mock_sleep, mock_filter, mock_get_client):
        """Test handle loop when no deployments are running."""
        mock_qs = MagicMock()
        mock_qs.exclude.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.exists.return_value = False
        mock_filter.return_value = mock_qs

        mock_sleep.side_effect = KeyboardInterrupt()

        out = StringIO()
        # Mocking self.stdout.write to NOT pass ending parameter to StringIO.write
        self.command.stdout = MagicMock()
        self.command.stdout.write.side_effect = lambda msg, ending="\n": out.write(msg + ending)

        self.command.handle()
        self.assertIn("No running deployments found", out.getvalue())
        self.assertIn("Monitoring stopped.", out.getvalue())
        mock_flush.assert_called()

    @patch("projects.management.commands.monitor_containers.get_docker_client")
    @patch("projects.management.commands.monitor_containers.Deployment.objects.filter")
    @patch("projects.management.commands.monitor_containers.time.sleep")
    def test_handle_with_deployments(self, mock_sleep, mock_filter, mock_get_client):
        """Test handle loop with running deployments."""
        mock_dep = MagicMock()
        mock_dep.project.name = "TestProject"
        mock_dep.container_id = "abc123def456"

        mock_qs = MagicMock()
        mock_qs.exclude.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.__iter__.return_value = [mock_dep]
        mock_qs.exists.return_value = True
        mock_filter.return_value = mock_qs

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container
        mock_container.stats.return_value = {
            "cpu_stats": {"cpu_usage": {"total_usage": 0}, "system_cpu_usage": 0},
            "precpu_stats": {"cpu_usage": {"total_usage": 0}, "system_cpu_usage": 0},
            "memory_stats": {"usage": 0, "limit": 1}
        }

        # Trigger KeyboardInterrupt on the FIRST sleep
        mock_sleep.side_effect = KeyboardInterrupt()

        out = StringIO()
        self.command.stdout = MagicMock()
        self.command.stdout.write.side_effect = lambda msg, ending="\n": out.write(msg + ending)
        self.command.stdout.style = MagicMock()

        self.command.handle()
        self.assertIn("Khamal Monitoring", out.getvalue())
        self.assertIn("TestProject", out.getvalue())
        self.assertIn("abc123def456", out.getvalue())
        self.assertIn("Monitoring stopped.", out.getvalue())

    @patch("projects.management.commands.monitor_containers.get_docker_client")
    @patch("projects.management.commands.monitor_containers.Deployment.objects.filter")
    @patch("projects.management.commands.monitor_containers.time.sleep")
    def test_handle_container_not_found(self, mock_sleep, mock_filter, mock_get_client):
        """Test handle when a container is not found."""
        mock_dep = MagicMock()
        mock_dep.project.name = "MissingProject"
        mock_dep.container_id = "missing_id"

        mock_qs = MagicMock()
        mock_qs.exclude.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.__iter__.return_value = [mock_dep]
        mock_qs.exists.return_value = True
        mock_filter.return_value = mock_qs

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = NotFound("Container not found")

        mock_sleep.side_effect = KeyboardInterrupt()

        out = StringIO()
        self.command.stdout = MagicMock()
        self.command.stdout.write.side_effect = lambda msg, ending="\n": out.write(msg + ending)
        self.command.stdout.style = MagicMock()

        self.command.handle()
        self.assertIn("Container missing_id for MissingProject not found.", out.getvalue())

    @patch("projects.management.commands.monitor_containers.get_docker_client")
    @patch("projects.management.commands.monitor_containers.Deployment.objects.filter")
    @patch("projects.management.commands.monitor_containers.time.sleep")
    def test_handle_general_exception(self, mock_sleep, mock_filter, mock_get_client):
        """Test handle when a general exception occurs for a container."""
        mock_dep = MagicMock()
        mock_dep.project.name = "ErrorProject"
        mock_dep.container_id = "error_id"

        mock_qs = MagicMock()
        mock_qs.exclude.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.__iter__.return_value = [mock_dep]
        mock_qs.exists.return_value = True
        mock_filter.return_value = mock_qs

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = Exception("Unexpected error")

        mock_sleep.side_effect = KeyboardInterrupt()

        out = StringIO()
        self.command.stdout = MagicMock()
        self.command.stdout.write.side_effect = lambda msg, ending="\n": out.write(msg + ending)
        self.command.stdout.style = MagicMock()

        self.command.handle()
        self.assertIn("Error getting stats for ErrorProject: Unexpected error", out.getvalue())
