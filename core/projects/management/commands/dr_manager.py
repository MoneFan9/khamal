from django.core.management.base import BaseCommand, CommandError
from core.projects.models import Project, Backup
from core.projects.services import perform_database_backup, restore_database_backup

class Command(BaseCommand):
    help = "Disaster Recovery Manager for Khamal. Automates backup and restore runbooks."

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest="action", required=True)

        # Backup subcommand
        backup_parser = subparsers.add_parser("backup", help="Perform a database backup")
        backup_parser.add_argument("--project-id", type=int, required=True, help="ID of the project")
        backup_parser.add_argument("--engine", choices=["postgres", "redis"], required=True, help="Database engine")

        # Restore subcommand
        restore_parser = subparsers.add_parser("restore", help="Restore a database from backup")
        restore_parser.add_argument("--backup-id", type=int, required=True, help="ID of the backup to restore")

    def handle(self, *args, **options):
        action = options["action"]

        if action == "backup":
            self.handle_backup(options)
        elif action == "restore":
            self.handle_restore(options)

    def handle_backup(self, options):
        project_id = options["project_id"]
        engine = options["engine"]

        try:
            project = Project.objects.get(id=project_id)
            self.stdout.write(self.style.NOTICE(f"Starting backup for project {project.name} ({engine})..."))
            file_path = perform_database_backup(project, engine)
            self.stdout.write(self.style.SUCCESS(f"Backup successfully created: {file_path}"))
        except Project.DoesNotExist:
            raise CommandError(f"Project with ID {project_id} does not exist.")
        except Exception as e:
            raise CommandError(f"Backup failed: {str(e)}")

    def handle_restore(self, options):
        backup_id = options["backup_id"]

        try:
            backup = Backup.objects.get(id=backup_id)
            self.stdout.write(self.style.NOTICE(f"Starting restoration for project {backup.project.name} ({backup.engine}) from {backup.file_path}..."))
            restore_database_backup(backup)
            self.stdout.write(self.style.SUCCESS(f"Restoration completed successfully."))
        except Backup.DoesNotExist:
            raise CommandError(f"Backup with ID {backup_id} does not exist.")
        except Exception as e:
            raise CommandError(f"Restoration failed: {str(e)}")
