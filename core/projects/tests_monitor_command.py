import pytest
from io import StringIO
from unittest.mock import MagicMock, patch
from django.core.management import call_command
from projects.management.commands.monitor_containers import Command

@pytest.fixture
def monitor_command():
    return Command()

def test_calculate_cpu_percent(monitor_command):
    stats = {
        "cpu_stats": {
            "cpu_usage": {"total_usage": 1000},
            "system_cpu_usage": 10000,
            "online_cpus": 2
        },
        "precpu_stats": {
            "cpu_usage": {"total_usage": 500},
            "system_cpu_usage": 5000
        }
    }
    # (1000 - 500) / (10000 - 5000) * 2 * 100 = 500 / 5000 * 200 = 0.1 * 200 = 20.0
    cpu_p = monitor_command.calculate_cpu_percent(stats)
    assert cpu_p == 20.0

def test_calculate_cpu_percent_zero_delta(monitor_command):
    stats = {
        "cpu_stats": {"cpu_usage": {"total_usage": 1000}, "system_cpu_usage": 10000},
        "precpu_stats": {"cpu_usage": {"total_usage": 1000}, "system_cpu_usage": 10000}
    }
    cpu_p = monitor_command.calculate_cpu_percent(stats)
    assert cpu_p == 0.0

def test_calculate_mem_usage(monitor_command):
    stats = {
        "memory_stats": {
            "usage": 1024 * 1024 * 100, # 100MB
            "limit": 1024 * 1024 * 500, # 500MB
            "stats": {"inactive_file": 1024 * 1024 * 10} # 10MB cache
        }
    }
    used, limit, percent = monitor_command.calculate_mem_usage(stats)
    assert used == 1024 * 1024 * 90
    assert limit == 1024 * 1024 * 500
    assert percent == 18.0

def test_format_bytes(monitor_command):
    assert monitor_command.format_bytes(500) == "500.00B"
    assert monitor_command.format_bytes(1024 * 2.5) == "2.50KB"
    assert monitor_command.format_bytes(1024 * 1024 * 3.75) == "3.75MB"
    assert monitor_command.format_bytes(1024 * 1024 * 1024 * 1.2) == "1.20GB"

@pytest.mark.django_db
@patch("projects.management.commands.monitor_containers.get_docker_client")
@patch("projects.models.Deployment.objects.filter")
def test_monitor_containers_handle_no_deployments(mock_filter, mock_get_docker, monitor_command):
    out = StringIO()
    # Replace stdout.write to handle the ending argument
    monitor_command.stdout.write = lambda msg, ending='\n': out.write(msg + str(ending))

    mock_filter.return_value.exclude.return_value.select_related.return_value.exists.return_value = False

    with patch("time.sleep", side_effect=KeyboardInterrupt):
        monitor_command.handle()

    output = out.getvalue()
    assert "Starting real-time container monitoring" in output
    assert "No running deployments found" in output
    assert "Monitoring stopped." in output
