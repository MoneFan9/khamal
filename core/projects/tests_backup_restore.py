import os
import shutil
from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from projects.models import Project
from projects.services import provision_database
from projects.backup_services import backup_database, restore_database
import docker

User = get_user_model()

class BackupRestoreTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dr_user", password="password")
        self.project = Project.objects.create(name="DRProject", owner=self.user)
        # Ensure credentials exist
        self.project.db_postgres_password = "secure-postgres-pass"
        self.project.db_redis_password = "secure-redis-pass"
        self.project.save()

    @patch('projects.services.get_docker_client')
    @patch('projects.services.ensure_project_network')
    @patch('projects.services._wait_for_healthy')
    @patch('projects.backup_services.get_docker_client')
    def test_postgres_backup_restore_workflow(self, mock_backup_docker, mock_wait, mock_ensure_net, mock_services_docker):
        # 1. Setup Mocks
        mock_client = MagicMock()
        mock_services_docker.return_value = mock_client
        mock_backup_docker.return_value = mock_client

        mock_container = MagicMock()
        mock_container.id = "cont_123"
        mock_container.status = "running"
        mock_client.containers.get.return_value = mock_container

        # Mock low-level API for streaming backup
        mock_client.api.exec_create.return_value = {"Id": "exec_123"}
        mock_client.api.exec_start.return_value = [b"DUMMY SQL CONTENT"]
        mock_client.api.exec_inspect.return_value = {"ExitCode": 0}

        # 2. Backup
        backup_path = backup_database(self.project, "postgres")
        self.assertTrue(os.path.exists(backup_path))
        self.assertIn("postgres", backup_path)

        with open(backup_path, "rb") as f:
            self.assertEqual(f.read(), b"DUMMY SQL CONTENT")

        # 3. Restore
        # Reset mock for restore
        mock_container.exec_run.return_value = MagicMock(exit_code=0, output=b"Restore success")

        restore_database(self.project, "postgres", backup_path)

        # Verify put_archive was called (for the sql file) and exec_run for psql
        mock_container.put_archive.assert_called_once()
        mock_container.exec_run.assert_called_with(
            ["psql", "-U", "khamal", "-d", "khamal", "-f", "/tmp/restore.sql"],
            environment={"PGPASSWORD": self.project.db_postgres_password}
        )

        # Cleanup
        if os.path.exists(backup_path):
            os.remove(backup_path)

    @patch('projects.services.get_docker_client')
    @patch('projects.services.ensure_project_network')
    @patch('projects.services._wait_for_healthy')
    @patch('projects.backup_services.get_docker_client')
    def test_redis_backup_restore_workflow(self, mock_backup_docker, mock_wait, mock_ensure_net, mock_services_docker):
        # 1. Setup Mocks
        mock_client = MagicMock()
        mock_services_docker.return_value = mock_client
        mock_backup_docker.return_value = mock_client

        mock_container = MagicMock()
        mock_container.status = "running"
        mock_client.containers.get.return_value = mock_container

        # Mock redis SAVE
        mock_container.exec_run.return_value = MagicMock(exit_code=0, output=b"OK")

        # Mock get_archive for Redis
        import io
        import tarfile
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            content = b"REDIS RDB CONTENT"
            tarinfo = tarfile.TarInfo(name="dump.rdb")
            tarinfo.size = len(content)
            tar.addfile(tarinfo, io.BytesIO(content))
        tar_stream.seek(0)

        mock_container.get_archive.return_value = (iter([tar_stream.getvalue()]), MagicMock())

        # 2. Backup
        backup_path = backup_database(self.project, "redis")
        self.assertTrue(os.path.exists(backup_path))

        with open(backup_path, "rb") as f:
            self.assertEqual(f.read(), b"REDIS RDB CONTENT")

        # 3. Restore
        restore_database(self.project, "redis", backup_path)

        # Verify Redis stop, put_archive, start
        mock_container.stop.assert_called_once()
        mock_container.put_archive.assert_called_once()
        mock_container.start.assert_called_once()

        # Cleanup
        if os.path.exists(backup_path):
            os.remove(backup_path)
