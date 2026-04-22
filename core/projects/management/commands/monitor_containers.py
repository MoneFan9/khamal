import time
import sys
from django.core.management.base import BaseCommand
from projects.docker_client import get_docker_client
from projects.models import Deployment
from docker.errors import NotFound

class Command(BaseCommand):
    help = "Monitor CPU and RAM usage of running containers in real-time."

    def calculate_cpu_percent(self, stats):
        """
        Calculates CPU percentage from docker stats.
        Formula: (cpu_delta / system_delta) * online_cpus * 100.0
        """
        cpu_stats = stats.get("cpu_stats", {})
        precpu_stats = stats.get("precpu_stats", {})

        cpu_usage = cpu_stats.get("cpu_usage", {})
        precpu_usage = precpu_stats.get("cpu_usage", {})

        cpu_delta = cpu_usage.get("total_usage", 0) - precpu_usage.get("total_usage", 0)
        system_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get("system_cpu_usage", 0)

        online_cpus = cpu_stats.get("online_cpus", len(cpu_usage.get("percpu_usage", [])) or 1)

        if system_delta > 0.0 and cpu_delta > 0.0:
            return (cpu_delta / system_delta) * online_cpus * 100.0
        return 0.0

    def calculate_mem_usage(self, stats):
        """
        Calculates Memory usage and percentage from docker stats.
        Returns (used_memory, limit, percent).
        """
        mem_stats = stats.get("memory_stats", {})
        usage = mem_stats.get("usage", 0)
        # Typically cache is subtracted from usage for a more accurate "active" memory
        cache = mem_stats.get("stats", {}).get("inactive_file", mem_stats.get("stats", {}).get("cache", 0))
        used_memory = usage - cache
        limit = mem_stats.get("limit", 1)

        percent = (used_memory / limit) * 100.0 if limit > 0 else 0
        return used_memory, limit, percent

    def format_bytes(self, size):
        power = 1024
        n = 0
        power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
        while size > power and n < 4:
            size /= power
            n += 1
        return f"{size:.2f}{power_labels[n]}B"

    def handle(self, *args, **options):
        client = get_docker_client()
        self.stdout.write(self.style.SUCCESS("Starting real-time container monitoring... (Ctrl+C to stop)"))

        try:
            while True:
                deployments = Deployment.objects.filter(status=Deployment.Status.RUNNING).exclude(container_id__isnull=True)

                if not deployments.exists():
                    self.stdout.write("No running deployments found. Waiting...", ending="\r")
                    sys.stdout.flush()
                    time.sleep(2)
                    continue

                # Clear screen and move to top
                self.stdout.write("\033[H\033[J")
                self.stdout.write(self.style.SUCCESS(f"Khamal Monitoring - {time.strftime('%Y-%m-%d %H:%M:%S')}"))
                self.stdout.write("")

                header = f"{'PROJECT':<20} {'CONTAINER ID':<15} {'CPU %':<10} {'MEM USAGE / LIMIT':<25} {'MEM %':<10}"
                self.stdout.write(self.style.MIGRATE_LABEL(header))
                self.stdout.write("-" * len(header))

                for dep in deployments:
                    try:
                        container = client.containers.get(dep.container_id)
                        stats = container.stats(stream=False)

                        cpu_p = self.calculate_cpu_percent(stats)
                        mem_used, mem_limit, mem_p = self.calculate_mem_usage(stats)

                        mem_str = f"{self.format_bytes(mem_used)} / {self.format_bytes(mem_limit)}"

                        line = f"{dep.project.name[:20]:<20} {dep.container_id[:12]:<15} {cpu_p:>6.2f}%    {mem_str:<25} {mem_p:>6.2f}%"
                        self.stdout.write(line)
                    except NotFound:
                        self.stdout.write(self.style.WARNING(f"Container {dep.container_id} for {dep.project.name} not found."))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error getting stats for {dep.project.name}: {e}"))

                time.sleep(2)
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS("\nMonitoring stopped."))
