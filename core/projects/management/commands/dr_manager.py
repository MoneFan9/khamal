import os
import tarfile
import io
from django.core.management.base import BaseCommand, CommandError
from projects.models import Project, DatabaseInstance
from projects.services import provision_database, get_docker_client
import docker

class Command(BaseCommand):
    help = "Disaster Recovery Manager: Backup and Restore project databases."

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["backup", "restore"], help="Action to perform")
        parser.add_argument("--project-id", type=int, required=True, help="ID of the project")
        parser.add_argument("--engine", choices=["postgres", "redis"], required=True, help="Database engine")
        parser.add_argument("--file", type=str, required=True, help="Backup file path")

    def handle(self, *args, **options):
        action = options["action"]
        project_id = options["project_id"]
        engine = options["engine"]
        file_path = options["file"]

        try:
            project = Project.objects.get(id=project_id)
            db_inst = DatabaseInstance.objects.get(project=project, engine=engine)
        except Project.DoesNotExist:
            raise CommandError(f"Project {project_id} not found")
        except DatabaseInstance.DoesNotExist:
            raise CommandError(f"DatabaseInstance for {engine} in project {project_id} not found")

        client = get_docker_client()
        container_name = f"khamal-db-{engine}-{project.id}"

        if action == "backup":
            self.do_backup(client, container_name, engine, db_inst, file_path)
        elif action == "restore":
            self.do_restore(client, project, container_name, engine, db_inst, file_path)

    def do_backup(self, client, container_name, engine, db_inst, file_path):
        try:
            container = client.containers.get(container_name)
        except docker.errors.NotFound:
            raise CommandError(f"Container {container_name} not found")

        self.stdout.write(f"Starting backup for {engine} in {container_name}...")

        if engine == "postgres":
            # Use pg_dump via low-level API for streaming
            # Use --clean to ensure restore drops existing objects
            # SECURITY: Use shlex.quote or avoid shell=True if we were using it,
            # here we pass args as a list to avoid injection.
            cmd = ["pg_dump", "-U", db_inst.db_user, "-d", db_inst.db_name, "--clean"]

            exec_id = client.api.exec_create(
                container.id,
                cmd,
                environment={"PGPASSWORD": db_inst.db_password}
            )["Id"]

            # demux=True returns a generator of (stdout, stderr) tuples
            # This avoids the 8-byte multiplex header that corrupts backups
            output_gen = client.api.exec_start(exec_id, stream=True, demux=True)

            with open(file_path, "wb") as f:
                for stdout_chunk, stderr_chunk in output_gen:
                    if stdout_chunk:
                        f.write(stdout_chunk)
                    if stderr_chunk:
                        self.stderr.write(stderr_chunk.decode('utf-8', errors='replace'))

            exit_code = client.api.exec_inspect(exec_id)["ExitCode"]
            if exit_code != 0:
                raise CommandError(f"pg_dump failed with exit code {exit_code}")

        elif engine == "redis":
            # Use redis-cli SAVE then get_archive
            env = {"REDISCLI_AUTH": db_inst.db_password} if db_inst.db_password else {}
            res = container.exec_run(["redis-cli", "SAVE"], environment=env)
            if res.exit_code != 0:
                raise CommandError(f"Redis SAVE failed: {res.output.decode()}")

            # get_archive returns a tuple (generator, stat)
            stream, stat = container.get_archive("/data/dump.rdb")
            with open(file_path, "wb") as f:
                for chunk in stream:
                    f.write(chunk)

        self.stdout.write(self.style.SUCCESS(f"Backup saved to {file_path}"))

    def do_restore(self, client, project, container_name, engine, db_inst, file_path):
        if not os.path.exists(file_path):
            raise CommandError(f"Backup file {file_path} not found")

        self.stdout.write(f"Starting restore for {engine} in {container_name}...")

        # Ensure container is running
        container = provision_database(project, engine)

        if engine == "postgres":
            # Stream the backup file into the container as a tar
            with open(file_path, "rb") as f:
                tar_stream = self._create_tar_stream("restore.sql", f)
                client.api.put_archive(container.id, "/tmp", tar_stream)

            cmd = ["psql", "-U", db_inst.db_user, "-d", db_inst.db_name, "-f", "/tmp/restore.sql"]
            res = container.exec_run(cmd, environment={"PGPASSWORD": db_inst.db_password})
            if res.exit_code != 0:
                raise CommandError(f"psql restore failed: {res.output.decode()}")

        elif engine == "redis":
            # Stop the container before putting the archive to avoid race conditions/overwrites
            container.stop()

            with open(file_path, "rb") as f:
                # Backup is already a tar containing 'dump.rdb'
                # We put it in /data/
                client.api.put_archive(container.id, "/data/", f)

            # Start again to load the new dump.rdb
            container.start()

        self.stdout.write(self.style.SUCCESS(f"Restore from {file_path} completed"))

    def _create_tar_stream(self, name, fileobj):
        """
        Creates a tar stream from a file object.
        """
        file_out = io.BytesIO()
        with tarfile.open(fileobj=file_out, mode="w") as tar:
            # We need to know the size for TarInfo
            fileobj.seek(0, os.SEEK_END)
            size = fileobj.tell()
            fileobj.seek(0)

            info = tarfile.TarInfo(name=name)
            info.size = size
            tar.addfile(info, fileobj)
        file_out.seek(0)
        return file_out
