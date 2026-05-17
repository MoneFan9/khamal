from django.core.management.base import BaseCommand, CommandError
from projects.models import Project, Database
from projects.backup_manager import BackupManager, BackupError

class Command(BaseCommand):
    help = "Triggers a backup for a project's database"

    def add_arguments(self, parser):
        parser.add_argument("project_id", type=int, help="ID of the project")
        parser.add_argument("engine", type=str, choices=["postgres", "redis"], help="Database engine")

    def handle(self, *args, **options):
        project_id = options["project_id"]
        engine = options["engine"]

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise CommandError(f"Project {project_id} does not exist")

        self.stdout.write(f"Starting backup for {engine} in project {project.name}...")

        manager = BackupManager()
        try:
            backup_path = manager.backup(project, engine)
            self.stdout.write(self.style.SUCCESS(f"Backup successful: {backup_path}"))
        except BackupError as e:
            raise CommandError(f"Backup failed: {e}")
