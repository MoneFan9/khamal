from django.core.management.base import BaseCommand
from projects.models import Project
from projects.dr import run_dr_validation
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Runs automated Disaster Recovery runbooks for projects."

    def add_arguments(self, parser):
        parser.add_argument('--project-id', type=int, help='ID of the project to test')
        parser.add_argument('--engine', type=str, choices=['postgres', 'redis', 'all'], default='all', help='DB engine to test')

    def handle(self, *args, **options):
        project_id = options['project_id']
        engine = options['engine']

        if project_id:
            projects = Project.objects.filter(id=project_id)
        else:
            projects = Project.objects.all()

        if not projects.exists():
            self.stdout.write(self.style.ERROR("No projects found."))
            return

        engines = ['postgres', 'redis'] if engine == 'all' else [engine]

        for project in projects:
            self.stdout.write(self.style.SUCCESS(f"Testing DR for project: {project.name} (ID: {project.id})"))
            for eng in engines:
                try:
                    self.stdout.write(f"  Testing {eng}...")
                    run_dr_validation(project, eng)
                    self.stdout.write(self.style.SUCCESS(f"  {eng} DR test passed!"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  {eng} DR test failed: {e}"))
