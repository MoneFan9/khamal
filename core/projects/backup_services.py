import docker
import logging
from .docker_client import get_docker_client
from .models import Project
import os
import tarfile
import io
import tempfile

logger = logging.getLogger(__name__)

def backup_project_database(project: Project, engine: str, backup_path: str):
    """
    Backs up a project's database to a file.
    """
    client = get_docker_client()
    container_name = f"khamal-db-{engine}-{project.id}"

    try:
        container = client.containers.get(container_name)
    except docker.errors.NotFound:
        logger.error(f"Container {container_name} not found for backup.")
        raise Exception(f"Database container {container_name} not found.")

    if engine == "postgres":
        # Stream the backup to avoid loading it into memory
        cmd = f"pg_dump -U khamal -d khamal"
        res = container.exec_run(cmd, stream=True, environment={"PGPASSWORD": project.db_postgres_password})

        with open(backup_path, 'wb') as f:
            for chunk in res.output:
                f.write(chunk)

        logger.info(f"PostgreSQL backup for project {project.id} saved to {backup_path}")

    elif engine == "redis":
        # For Redis, we use redis-cli --rdb to stream the backup
        cmd = f"redis-cli -a {project.db_redis_password} --no-auth-warning --rdb -"
        res = container.exec_run(cmd, stream=True)

        with open(backup_path, 'wb') as f:
            for chunk in res.output:
                f.write(chunk)

        logger.info(f"Redis backup for project {project.id} saved to {backup_path}")
    else:
        raise NotImplementedError(f"Backup not implemented for engine: {engine}")

def restore_project_database(project: Project, engine: str, backup_path: str):
    """
    Restores a project's database from a file.
    """
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file {backup_path} not found.")

    client = get_docker_client()
    container_name = f"khamal-db-{engine}-{project.id}"

    try:
        container = client.containers.get(container_name)
    except docker.errors.NotFound:
        logger.error(f"Container {container_name} not found for restore.")
        raise Exception(f"Database container {container_name} not found.")

    if engine == "postgres":
        # PostgreSQL restore using psql
        # To be memory efficient, we create a temporary tar file instead of using BytesIO
        with tempfile.NamedTemporaryFile() as tmp_tar:
            with tarfile.open(fileobj=tmp_tar, mode='w') as tar:
                tar.add(backup_path, arcname="restore.sql")

            tmp_tar.seek(0)
            container.put_archive("/tmp/", tmp_tar)

        res = container.exec_run(
            f"sh -c 'psql -U khamal -d khamal < /tmp/restore.sql && rm /tmp/restore.sql'",
            environment={"PGPASSWORD": project.db_postgres_password}
        )

        if res.exit_code != 0:
            logger.error(f"Restore failed: {res.output.decode()}")
            raise Exception(f"PostgreSQL restore failed with exit code {res.exit_code}")

        logger.info(f"PostgreSQL restore for project {project.id} completed.")

    elif engine == "redis":
        # 1. Stop container (to safely replace RDB)
        container.stop()

        volume_name = f"khamal-data-redis-{project.id}"

        # Create a helper container to overwrite the dump.rdb
        # We stream the file content to the helper container's stdin
        helper = client.containers.run(
            "alpine",
            command="sh -c 'cat > /data/dump.rdb'",
            volumes={volume_name: {'bind': '/data', 'mode': 'rw'}},
            detach=True,
            stdin_open=True
        )

        with open(backup_path, 'rb') as f:
            sock = helper.attach_socket(params={'stdin': 1, 'stream': 1})
            # Use a loop to stream in chunks for memory efficiency
            while True:
                chunk = f.read(1024 * 1024) # 1MB chunks
                if not chunk:
                    break
                sock._sock.sendall(chunk)
            sock.close()

        helper.wait()
        helper.remove()

        # 3. Start container
        container.start()
        logger.info(f"Redis restore for project {project.id} completed.")

    else:
        raise NotImplementedError(f"Restore not implemented for engine: {engine}")
