from django.core.management.base import BaseCommand, CommandError
from projects.models import Project, Database
from projects.backup_manager import BackupManager, BackupError

class Command(BaseCommand):
    help = "Restores a project's database from a backup file"

    def add_arguments(self, parser):
        parser.add_argument("project_id", type=int, help="ID of the project")
        parser.add_argument("engine", type=str, choices=["postgres", "redis"], help="Database engine")
        parser.add_argument("backup_path", type=str, help="Path to the backup file")

    def handle(self, *args, **options):
        project_id = options["project_id"]
        engine = options["engine"]
        backup_path = options["backup_path"]

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise CommandError(f"Project {project_id} does not exist")

        self.stdout.write(f"Restoring {engine} for project {project.name} from {backup_path}...")

        manager = BackupManager()
        try:
            manager.restore(project, engine, backup_path)
            self.stdout.write(self.style.SUCCESS("Restoration successful"))
        except BackupError as e:
            raise CommandError(f"Restoration failed: {e}")
