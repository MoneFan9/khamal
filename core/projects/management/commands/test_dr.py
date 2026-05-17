from django.core.management.base import BaseCommand, CommandError
from projects.models import Project, Database
from projects.backup_manager import BackupManager, BackupError
from projects.services import provision_database, get_docker_client
import docker
import time

class Command(BaseCommand):
    help = "Automates a full Disaster Recovery test for a project"

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

        manager = BackupManager()
        client = get_docker_client()
        db_obj = Database.objects.get(project=project, engine=engine)

        self.stdout.write(f"--- Starting DR Test for {project.name} ({engine}) ---")

        # 1. Provision & Populate
        self.stdout.write("1. Provisioning database...")
        container = provision_database(project, engine)

        self.stdout.write("2. Populating test data...")
        if engine == "postgres":
            container.exec_run(f"psql -U {db_obj.db_user} -d {db_obj.db_name} -c 'CREATE TABLE dr_test (val TEXT); INSERT INTO dr_test VALUES (''Khamal-Safe'');'",
                               environment={"PGPASSWORD": db_obj.db_password})
        else:
            container.exec_run("redis-cli SET dr_test Khamal-Safe")

        # 2. Backup
        self.stdout.write("3. Creating backup...")
        backup_path = manager.backup(project, engine)
        self.stdout.write(f"   Backup path: {backup_path}")

        # 3. Simulate Total Loss (Wipe)
        self.stdout.write("4. Simulating TOTAL LOSS (deleting container and volume)...")
        container.remove(force=True)
        volume_name = f"khamal-data-{engine}-{project.id}"
        try:
            volume = client.volumes.get(volume_name)
            volume.remove(force=True)
        except docker.errors.NotFound:
            pass

        # 4. Restore
        self.stdout.write("5. Re-provisioning (Empty Database)...")
        container = provision_database(project, engine)

        self.stdout.write("6. Restoring from backup...")
        manager.restore(project, engine, backup_path)

        # 5. Verify Integrity
        self.stdout.write("7. Verifying data integrity...")
        if engine == "postgres":
            res = container.exec_run(f"psql -U {db_obj.db_user} -d {db_obj.db_name} -t -c 'SELECT val FROM dr_test;'",
                                     environment={"PGPASSWORD": db_obj.db_password})
            val = res.output.decode().strip()
        else:
            res = container.exec_run("redis-cli GET dr_test")
            val = res.output.decode().strip()

        if val == "Khamal-Safe":
            self.stdout.write(self.style.SUCCESS("DR TEST SUCCESSFUL: Data recovered perfectly!"))
        else:
            self.stdout.write(self.style.ERROR(f"DR TEST FAILED: Got '{val}' instead of 'Khamal-Safe'"))
            raise CommandError("Data integrity check failed")
