from django.core.management.base import BaseCommand, CommandError
from projects.models import Project
from projects.backup_services import backup_project_database
import os
from django.utils import timezone

class Command(BaseCommand):
    help = 'Backs up the database of a project'

    def add_arguments(self, parser):
        parser.add_argument('project_id', type=int)
        parser.add_argument('--engine', type=str, default='postgres', choices=['postgres', 'redis'])
        parser.add_argument('--output', type=str, help='Output file path')

    def handle(self, *args, **options):
        project_id = options['project_id']
        engine = options['engine']

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise CommandError(f"Project {project_id} does not exist")

        if options['output']:
            backup_path = options['output']
        else:
            timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
            ext = 'sql' if engine == 'postgres' else 'rdb'
            backup_path = f"backup_{project.name}_{engine}_{timestamp}.{ext}"

        self.stdout.write(self.style.NOTICE(f"Starting backup for project {project.name} ({engine})..."))

        try:
            backup_project_database(project, engine, backup_path)
            self.stdout.write(self.style.SUCCESS(f"Successfully backed up to {backup_path}"))
        except Exception as e:
            raise CommandError(f"Backup failed: {str(e)}")
