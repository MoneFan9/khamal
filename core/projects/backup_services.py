import os
import logging
import subprocess
import datetime
from django.conf import settings
from .models import Project
from .docker_client import get_docker_client
import docker

logger = logging.getLogger(__name__)

BACKUP_DIR = os.path.join(settings.BASE_DIR, "backups")

def ensure_backup_dir():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR, exist_ok=True)

def backup_database(project: Project, engine: str) -> str:
    """
    Performs a backup of the specified database engine for the project.
    Returns the path to the backup file.
    """
    ensure_backup_dir()
    client = get_docker_client()
    container_name = f"khamal-db-{engine}-{project.id}"

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_filename = f"{container_name}_{timestamp}"

    try:
        container = client.containers.get(container_name)
    except docker.errors.NotFound:
        logger.error(f"Container {container_name} not found for backup.")
        raise Exception(f"Container {container_name} not found.")

    if engine == "postgres":
        backup_path = os.path.join(BACKUP_DIR, f"{backup_filename}.sql")
        env = {"PGPASSWORD": project.db_postgres_password}
        cmd = ["pg_dump", "-U", "khamal", "-d", "khamal"]

        # Stream the output to avoid loading the entire dump into memory
        exec_id = client.api.exec_create(container.id, cmd, environment=env)["Id"]
        output_gen = client.api.exec_start(exec_id, stream=True)

        with open(backup_path, "wb") as f:
            for chunk in output_gen:
                f.write(chunk)

        # Check exit code
        inspect = client.api.exec_inspect(exec_id)
        if inspect["ExitCode"] != 0:
            logger.error(f"pg_dump failed for {container_name} (Exit: {inspect['ExitCode']})")
            if os.path.exists(backup_path):
                os.remove(backup_path)
            raise Exception(f"Backup failed with exit code {inspect['ExitCode']}")

        logger.info(f"PostgreSQL backup created at {backup_path}")
        return backup_path

    elif engine == "redis":
        backup_path = os.path.join(BACKUP_DIR, f"{backup_filename}.rdb")
        # Trigger SAVE
        res = container.exec_run(["redis-cli", "SAVE"])
        if res.exit_code != 0:
            error_msg = res.output.decode('utf-8')
            logger.error(f"Redis SAVE failed for {container_name}: {error_msg}")
            raise Exception(f"Backup failed: {error_msg}")

        # Copy /data/dump.rdb from container to host
        # docker-py copy uses a tar stream
        stream, stat = container.get_archive("/data/dump.rdb")

        tar_path = backup_path + ".tar"
        with open(tar_path, "wb") as f:
            for chunk in stream:
                f.write(chunk)

        # Extract from tar
        import tarfile
        with tarfile.open(tar_path) as tar:
            # Redis dump is usually just dump.rdb at the root of the tar if we requested /data/dump.rdb
            # Actually get_archive of a file returns a tar containing that file.
            member = tar.getmember("dump.rdb")
            f = tar.extractfile(member)
            with open(backup_path, "wb") as target:
                target.write(f.read())

        os.remove(tar_path)
        logger.info(f"Redis backup created at {backup_path}")
        return backup_path

    else:
        raise ValueError(f"Unsupported engine: {engine}")

def restore_database(project: Project, engine: str, backup_path: str):
    """
    Restores the database from a backup file.
    """
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    client = get_docker_client()
    container_name = f"khamal-db-{engine}-{project.id}"

    try:
        container = client.containers.get(container_name)
    except docker.errors.NotFound:
        # Re-provision if not found?
        # For now, expect it to exist (provision_database should be called first if needed)
        logger.error(f"Container {container_name} not found for restore.")
        raise Exception(f"Container {container_name} not found. Please provision it first.")

    if engine == "postgres":
        with open(backup_path, "rb") as f:
            content = f.read()

        env = {"PGPASSWORD": project.db_postgres_password}
        # Drop and recreate schema might be cleaner, but psql -d khamal will run the dump
        # The dump from pg_dump usually contains everything needed.
        cmd = ["psql", "-U", "khamal", "-d", "khamal"]

        # res = container.exec_run(cmd, environment=env, stdin=True)
        # Note: docker-py exec_run doesn't support stdin easily in this way.
        # Alternative: copy file to container then run psql -f

        container.put_archive("/tmp", _create_tar_with_content("restore.sql", content))
        res = container.exec_run(["psql", "-U", "khamal", "-d", "khamal", "-f", "/tmp/restore.sql"], environment=env)

        if res.exit_code != 0:
            error_msg = res.output.decode('utf-8')
            logger.error(f"psql restore failed for {container_name}: {error_msg}")
            raise Exception(f"Restore failed: {error_msg}")

        logger.info(f"PostgreSQL restore completed from {backup_path}")

    elif engine == "redis":
        # Redis restore: stop container, replace dump.rdb, start container
        container.stop()

        # We need the volume name to replace the file or use put_archive while it's stopped?
        # Actually put_archive works on stopped containers.
        with open(backup_path, "rb") as f:
            content = f.read()

        container.put_archive("/data", _create_tar_with_content("dump.rdb", content))
        container.start()
        logger.info(f"Redis restore completed from {backup_path}")

    else:
        raise ValueError(f"Unsupported engine: {engine}")

def _create_tar_with_content(name, content):
    import io
    import tarfile

    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
        tarinfo = tarfile.TarInfo(name=name)
        tarinfo.size = len(content)
        tar.addfile(tarinfo, io.BytesIO(content))
    return tar_stream.getvalue()
