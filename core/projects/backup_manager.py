import logging
import os
import time
import tarfile
import io
import docker
from django.conf import settings
from .docker_client import get_docker_client
from .models import Project, Database

logger = logging.getLogger(__name__)

class BackupError(Exception):
    pass

class BackupManager:
    """
    Handles backups and restores for project databases.
    Implemented with streaming to handle large databases and demuxing to avoid corruption.
    """
    BACKUP_DIR = os.path.join(settings.MEDIA_ROOT, 'backups')

    def __init__(self):
        self.client = get_docker_client()
        os.makedirs(self.BACKUP_DIR, exist_ok=True)

    def _get_container(self, project: Project, engine: str):
        container_name = f"khamal-db-{engine}-{project.id}"
        try:
            return self.client.containers.get(container_name)
        except docker.errors.NotFound:
            raise BackupError(f"Container {container_name} not found")

    def backup(self, project: Project, engine: str) -> str:
        """
        Triggers a backup for the given project and engine.
        Returns the path to the backup file.
        """
        if engine == Database.Engine.POSTGRES:
            return self._backup_postgres(project)
        elif engine == Database.Engine.REDIS:
            return self._backup_redis(project)
        else:
            raise BackupError(f"Unsupported engine: {engine}")

    def restore(self, project: Project, engine: str, backup_path: str):
        """
        Restores a backup for the given project and engine.
        """
        if engine == Database.Engine.POSTGRES:
            self._restore_postgres(project, backup_path)
        elif engine == Database.Engine.REDIS:
            self._restore_redis(project, backup_path)
        else:
            raise BackupError(f"Unsupported engine: {engine}")

    def _backup_postgres(self, project: Project) -> str:
        container = self._get_container(project, Database.Engine.POSTGRES)
        db_obj = Database.objects.get(project=project, engine=Database.Engine.POSTGRES)

        timestamp = int(time.time())
        filename = f"postgres-{project.id}-{timestamp}.sql"
        local_path = os.path.join(self.BACKUP_DIR, filename)

        cmd = ["pg_dump", "-U", db_obj.db_user, "-d", db_obj.db_name]

        # Use demux=True to separate stdout (backup data) from stderr (logs/errors)
        # However, exec_run with demux=True doesn't stream.
        # For true streaming of large data, we use socket=True.

        try:
            exec_id = self.client.api.exec_create(
                container.id,
                cmd,
                environment={"PGPASSWORD": db_obj.db_password}
            )['Id']

            output_gen = self.client.api.exec_start(exec_id, stream=True, demux=True)

            with open(local_path, 'wb') as f:
                for stdout_chunk, stderr_chunk in output_gen:
                    if stdout_chunk:
                        f.write(stdout_chunk)
                    if stderr_chunk:
                        logger.warning(f"pg_dump stderr: {stderr_chunk.decode().strip()}")

            inspect_res = self.client.api.exec_inspect(exec_id)
            if inspect_res['ExitCode'] != 0:
                if os.path.exists(local_path):
                    os.remove(local_path)
                raise BackupError(f"pg_dump failed with exit code {inspect_res['ExitCode']}")

        except Exception as e:
            if not isinstance(e, BackupError):
                logger.exception("Unexpected error during PostgreSQL backup")
            raise BackupError(f"PostgreSQL backup failed: {e}")

        logger.info(f"PostgreSQL backup created for project {project.id}: {local_path}")
        return local_path

    def _restore_postgres(self, project: Project, backup_path: str):
        container = self._get_container(project, Database.Engine.POSTGRES)
        db_obj = Database.objects.get(project=project, engine=Database.Engine.POSTGRES)

        if not os.path.exists(backup_path):
            raise BackupError(f"Backup file not found: {backup_path}")

        container_tmp_path = f"/tmp/restore-{int(time.monotonic())}.sql"

        # Stream file into container using put_archive
        def tar_generator():
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                tarinfo = tarfile.TarInfo(name=os.path.basename(container_tmp_path))
                tarinfo.size = os.path.getsize(backup_path)
                with open(backup_path, 'rb') as f:
                    tar.addfile(tarinfo, f)
            return tar_stream.getvalue()

        try:
            container.put_archive("/tmp", tar_generator())

            # Execute restore via psql
            # We use a list to avoid shell injection, although we must use sh -c for redirect/piping if needed.
            # Here we use -f which takes a path.
            restore_cmd = ["psql", "-U", db_obj.db_user, "-d", db_obj.db_name, "-f", container_tmp_path]

            exec_res = container.exec_run(
                restore_cmd,
                environment={"PGPASSWORD": db_obj.db_password},
                demux=True
            )

            if exec_res.exit_code != 0:
                stderr = exec_res.output[1].decode() if exec_res.output[1] else "Unknown error"
                raise BackupError(f"psql restore failed: {stderr}")

        finally:
            container.exec_run(["rm", "-f", container_tmp_path])

        logger.info(f"PostgreSQL restoration complete for project {project.id}")

    def _backup_redis(self, project: Project) -> str:
        container = self._get_container(project, Database.Engine.REDIS)

        exec_result = container.exec_run("redis-cli SAVE")
        if exec_result.exit_code != 0:
            raise BackupError(f"Redis SAVE failed: {exec_result.output.decode()}")

        timestamp = int(time.time())
        filename = f"redis-{project.id}-{timestamp}.rdb"
        local_path = os.path.join(self.BACKUP_DIR, filename)

        try:
            bits, stat = container.get_archive("/data/dump.rdb")

            # bits is a generator of chunks from the tar stream
            tar_stream = io.BytesIO()
            with open(local_path, 'wb') as local_f:
                # We need to untar it on the fly or just use a temporary tar file
                # For simplicity and memory efficiency, we'll extract it using tarfile from the stream

                # We have to consume the generator
                import tempfile
                with tempfile.TemporaryFile() as tmp_tar:
                    for chunk in bits:
                        tmp_tar.write(chunk)
                    tmp_tar.seek(0)

                    with tarfile.open(fileobj=tmp_tar) as tar:
                        member = tar.getmember("dump.rdb")
                        f = tar.extractfile(member)
                        # Stream from extracted file to local path
                        while True:
                            chunk = f.read(64 * 1024)
                            if not chunk:
                                break
                            local_f.write(chunk)

        except Exception as e:
            raise BackupError(f"Failed to retrieve dump.rdb: {e}")

        logger.info(f"Redis backup created for project {project.id}: {local_path}")
        return local_path

    def _restore_redis(self, project: Project, backup_path: str):
        container = self._get_container(project, Database.Engine.REDIS)

        if not os.path.exists(backup_path):
            raise BackupError(f"Backup file not found: {backup_path}")

        # Stream into container
        def tar_generator():
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                tarinfo = tarfile.TarInfo(name="dump.rdb")
                tarinfo.size = os.path.getsize(backup_path)
                with open(backup_path, 'rb') as f:
                    tar.addfile(tarinfo, f)
            return tar_stream.getvalue()

        try:
            container.put_archive("/data", tar_generator())
            container.restart()
        except Exception as e:
            raise BackupError(f"Redis restore failed: {e}")

        logger.info(f"Redis restoration complete for project {project.id}")
