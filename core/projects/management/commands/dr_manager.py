from django.core.management.base import BaseCommand, CommandError
from projects.models import Project, DatabaseInstance, Backup
from projects.services import backup_database, restore_database
import sys

class Command(BaseCommand):
    help = "Orchestrates Disaster Recovery (DR) operations for Khamal databases."

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["backup", "restore", "list"], help="Action to perform")
        parser.add_argument("--project-id", type=int, help="Project ID")
        parser.add_argument("--engine", help="Database engine (postgres/redis)")
        parser.add_argument("--backup-id", type=int, help="Backup ID for restoration")

    def handle(self, *args, **options):
        action = options["action"]
        project_id = options.get("project_id")
        engine = options.get("engine")
        backup_id = options.get("backup_id")

        if action == "list":
            self.handle_list(project_id)
        elif action == "backup":
            self.handle_backup(project_id, engine)
        elif action == "restore":
            self.handle_restore(backup_id)

    def handle_list(self, project_id=None):
        instances = DatabaseInstance.objects.all()
        if project_id:
            instances = instances.filter(project_id=project_id)

        self.stdout.write(self.style.MIGRATE_HEADING("Database Instances:"))
        for inst in instances:
            self.stdout.write(f"- [{inst.id}] {inst.engine} for project {inst.project.name} (Container: {inst.container_name})")
            backups = inst.backups.order_by("-created_at")[:5]
            for b in backups:
                self.stdout.write(f"  * Backup {b.id}: {b.status} ({b.created_at})")

    def handle_backup(self, project_id, engine):
        if not project_id or not engine:
            raise CommandError("--project-id and --engine are required for backup.")

        try:
            instance = DatabaseInstance.objects.get(project_id=project_id, engine=engine)
            self.stdout.write(f"Starting backup for {instance}...")
            backup = backup_database(instance)
            if backup.status == Backup.Status.COMPLETED:
                self.stdout.write(self.style.SUCCESS(f"Backup successful: {backup.file_path}"))
            else:
                self.stdout.write(self.style.ERROR(f"Backup failed: {backup.error_message}"))
        except DatabaseInstance.DoesNotExist:
            raise CommandError(f"No {engine} instance found for project {project_id}")

    def handle_restore(self, backup_id):
        if not backup_id:
            raise CommandError("--backup-id is required for restoration.")

        try:
            backup = Backup.objects.get(id=backup_id)
            instance = backup.db_instance
            self.stdout.write(f"Starting restoration for {instance} from backup {backup.id}...")
            restore_database(instance, backup)
            self.stdout.write(self.style.SUCCESS("Restoration successful."))
        except Backup.DoesNotExist:
            raise CommandError(f"Backup {backup_id} not found.")
        except Exception as e:
            raise CommandError(f"Restoration failed: {e}")
