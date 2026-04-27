from django.test import TestCase
from unittest.mock import patch, MagicMock
from projects.management.commands.monitor_containers import Command

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
