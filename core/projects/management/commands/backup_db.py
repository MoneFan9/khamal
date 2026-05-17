from django.core.management.base import BaseCommand, CommandError
from projects.models import Project
from projects.backup_services import backup_database

class Command(BaseCommand):
    help = "Backs up a project's database."

    def add_arguments(self, parser):
        parser.add_argument("project_id", type=int, help="ID of the project")
        parser.add_argument("engine", type=str, help="Database engine (postgres or redis)")

    def handle(self, *args, **options):
        project_id = options["project_id"]
        engine = options["engine"]

        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            raise CommandError(f"Project with ID {project_id} does not exist.")

        self.stdout.write(self.style.NOTICE(f"Starting backup for {engine} (Project: {project.name})..."))
        try:
            backup_path = backup_database(project, engine)
            self.stdout.write(self.style.SUCCESS(f"Backup created successfully: {backup_path}"))
        except Exception as e:
            raise CommandError(f"Backup failed: {str(e)}")
