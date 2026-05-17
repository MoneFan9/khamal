from django.core.management.base import BaseCommand, CommandError
from projects.models import Project
from projects.backup_services import restore_database

class Command(BaseCommand):
    help = "Restores a project's database from a backup file."

    def add_arguments(self, parser):
        parser.add_argument("project_id", type=int, help="ID of the project")
        parser.add_argument("engine", type=str, help="Database engine (postgres or redis)")
        parser.add_argument("backup_path", type=str, help="Path to the backup file")

    def handle(self, *args, **options):
        project_id = options["project_id"]
        engine = options["engine"]
        backup_path = options["backup_path"]

        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            raise CommandError(f"Project with ID {project_id} does not exist.")

        self.stdout.write(self.style.NOTICE(f"Starting restoration for {engine} (Project: {project.name}) from {backup_path}..."))
        try:
            restore_database(project, engine, backup_path)
            self.stdout.write(self.style.SUCCESS(f"Restoration completed successfully."))
        except Exception as e:
            raise CommandError(f"Restoration failed: {str(e)}")
