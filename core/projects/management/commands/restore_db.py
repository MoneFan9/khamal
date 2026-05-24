from django.core.management.base import BaseCommand, CommandError
from projects.models import Project
from projects.backup_services import restore_project_database
import os

class Command(BaseCommand):
    help = 'Restores the database of a project from a backup file'

    def add_arguments(self, parser):
        parser.add_argument('project_id', type=int)
        parser.add_argument('backup_path', type=str)
        parser.add_argument('--engine', type=str, default='postgres', choices=['postgres', 'redis'])

    def handle(self, *args, **options):
        project_id = options['project_id']
        backup_path = options['backup_path']
        engine = options['engine']

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise CommandError(f"Project {project_id} does not exist")

        if not os.path.exists(backup_path):
            raise CommandError(f"Backup file {backup_path} does not exist")

        self.stdout.write(self.style.NOTICE(f"Starting restore for project {project.name} ({engine}) from {backup_path}..."))

        try:
            restore_project_database(project, engine, backup_path)
            self.stdout.write(self.style.SUCCESS(f"Successfully restored database for project {project.name}"))
        except Exception as e:
            raise CommandError(f"Restore failed: {str(e)}")
