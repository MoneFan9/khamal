import os
import logging
import time
import shutil
import tarfile
import io
import tempfile
from django.conf import settings
from .docker_client import get_docker_client
from .models import Project
from .services import provision_database
import docker

logger = logging.getLogger(__name__)

BACKUP_DIR = os.path.join(settings.BASE_DIR, "backups")

def ensure_backup_dir():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR, exist_ok=True)

def get_db_container(project: Project, engine: str):
    client = get_docker_client()
    container_name = f"khamal-db-{engine}-{project.id}"
    try:
        return client.containers.get(container_name)
    except docker.errors.NotFound:
        return None

def backup_database(project: Project, engine: str) -> str:
    """
    Performs a backup of the specified database engine for a project.
    Returns the path to the backup file.
    """
    ensure_backup_dir()
    container = get_db_container(project, engine)
    if not container or container.status != "running":
        raise Exception(f"Database container for {engine} is not running.")

    timestamp = int(time.time())
    if engine == "postgres":
        backup_path = os.path.join(BACKUP_DIR, f"backup-{project.id}-postgres-{timestamp}.sql")
        # Get password from environment
        env = container.attrs['Config']['Env']
        password = next((e.split('=')[1] for e in env if e.startswith('POSTGRES_PASSWORD=')), None)

        cmd = f"pg_dump -U khamal khamal"
        res = container.exec_run(cmd, environment={"PGPASSWORD": password})
        if res.exit_code != 0:
            raise Exception(f"pg_dump failed: {res.output.decode()}")

        with open(backup_path, "wb") as f:
            f.write(res.output)

        return backup_path

    elif engine == "redis":
        backup_path = os.path.join(BACKUP_DIR, f"backup-{project.id}-redis-{timestamp}.rdb")
        # Trigger SAVE
        res = container.exec_run("redis-cli SAVE")
        if res.exit_code != 0:
            raise Exception(f"Redis SAVE failed: {res.output.decode()}")

        # Stream the dump.rdb file from container
        bits, stat = container.get_archive("/data/dump.rdb")
        # get_archive returns a tar stream

        tar_stream = io.BytesIO()
        for chunk in bits:
            tar_stream.write(chunk)
        tar_stream.seek(0)

        with tarfile.open(fileobj=tar_stream) as tar:
            member = tar.getmember("dump.rdb")
            f = tar.extractfile(member)
            with open(backup_path, "wb") as bf:
                bf.write(f.read())

        return backup_path

    else:
        raise ValueError(f"Unsupported database engine: {engine}")

def restore_database(project: Project, engine: str, backup_path: str):
    """
    Restores a database from a backup file.
    """
    client = get_docker_client()
    container_name = f"khamal-db-{engine}-{project.id}"

    # Ensure container is running (provision if necessary)
    container = provision_database(project, engine)

    if engine == "postgres":
        with open(backup_path, "rb") as f:
            sql_content = f.read()

        env = container.attrs['Config']['Env']
        password = next((e.split('=')[1] for e in env if e.startswith('POSTGRES_PASSWORD=')), None)

        # Use psql to restore. We might need to drop and recreate the DB or just pipe it.
        # For simplicity, we assume we can just pipe it.
        # But pg_dump above might not include DROP TABLE.

        # Let's try to run psql and feed the content

        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(sql_content)
            tmp.flush()

            # Tar it up to use put_archive
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                tar.add(tmp.name, arcname="restore.sql")
            tar_stream.seek(0)
            container.put_archive("/tmp", tar_stream)

            res = container.exec_run(f"psql -U khamal khamal -f /tmp/restore.sql", environment={"PGPASSWORD": password})
            if res.exit_code != 0:
                raise Exception(f"psql restore failed: {res.output.decode()}")

    elif engine == "redis":
        # To restore Redis, we should stop it, replace dump.rdb, then start it.
        container.stop()

        # We need to find the volume path or use put_archive while it's stopped?
        # Actually put_archive works on stopped containers too.

        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            tar.add(backup_path, arcname="dump.rdb")
        tar_stream.seek(0)
        container.put_archive("/data", tar_stream)

        container.start()

    else:
        raise ValueError(f"Unsupported database engine: {engine}")

def run_dr_validation(project: Project, engine: str):
    """
    Automated runbook to test DR.
    """
    logger.info(f"Starting DR validation for {engine} on project {project.name}")

    # 1. Ensure DB is running
    container = provision_database(project, engine)

    # 2. Insert test data
    test_key = f"dr_test_{int(time.time())}"
    test_value = "khamal_is_awesome"

    if engine == "postgres":
        container.exec_run(f"psql -U khamal khamal -c \"CREATE TABLE IF NOT EXISTS dr_tests (key TEXT PRIMARY KEY, value TEXT);\"", environment={"PGPASSWORD": _get_pg_pass(container)})
        container.exec_run(f"psql -U khamal khamal -c \"INSERT INTO dr_tests (key, value) VALUES ('{test_key}', '{test_value}');\"", environment={"PGPASSWORD": _get_pg_pass(container)})
    elif engine == "redis":
        container.exec_run(f"redis-cli SET {test_key} {test_value}")

    # 3. Backup
    backup_path = backup_database(project, engine)
    logger.info(f"Backup created at {backup_path}")

    # 4. Simulate Disaster: Remove container and volume
    client = get_docker_client()
    container_name = container.name
    container.remove(force=True)

    volume_name = f"khamal-data-{engine}-{project.id}"
    try:
        volume = client.volumes.get(volume_name)
        volume.remove(force=True)
        logger.info(f"Disaster simulated: container {container_name} and volume {volume_name} removed.")
    except docker.errors.NotFound:
        pass

    # 5. Restore
    restore_database(project, engine, backup_path)
    logger.info(f"Restore completed from {backup_path}")

    # 6. Verify data
    new_container = get_db_container(project, engine)
    if engine == "postgres":
        res = new_container.exec_run(f"psql -U khamal khamal -c \"SELECT value FROM dr_tests WHERE key='{test_key}';\"", environment={"PGPASSWORD": _get_pg_pass(new_container)})
        output = res.output.decode()
        if test_value not in output:
            raise Exception(f"Verification failed: {test_value} not found in output: {output}")
    elif engine == "redis":
        res = new_container.exec_run(f"redis-cli GET {test_key}")
        output = res.output.decode().strip()
        if output != test_value:
            raise Exception(f"Verification failed: {test_value} != {output}")

    logger.info(f"DR validation for {engine} PASSED!")
    return True

def _get_pg_pass(container):
    env = container.attrs['Config']['Env']
    return next((e.split('=')[1] for e in env if e.startswith('POSTGRES_PASSWORD=')), None)
