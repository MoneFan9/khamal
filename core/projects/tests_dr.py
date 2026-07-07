from django.test import TestCase
from unittest.mock import patch, MagicMock
from .models import Project
from .dr import backup_database, restore_database, run_dr_validation
from django.contrib.auth import get_user_model
import docker
import os
import io
import tarfile

User = get_user_model()

class DRTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dr_user", password="password")
        self.project = Project.objects.create(name="DRProject", owner=self.user)

    @patch('projects.dr.get_docker_client')
    def test_backup_postgres(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_container = MagicMock()
        mock_container.status = "running"
        mock_container.attrs = {'Config': {'Env': ['POSTGRES_PASSWORD=secret']}}
        mock_container.exec_run.return_value = MagicMock(exit_code=0, output=b"SQL DUMP CONTENT")

        mock_client.containers.get.return_value = mock_container

        backup_path = backup_database(self.project, "postgres")

        self.assertTrue(os.path.exists(backup_path))
        with open(backup_path, "rb") as f:
            self.assertEqual(f.read(), b"SQL DUMP CONTENT")

        # Cleanup
        os.remove(backup_path)

    @patch('projects.dr.get_docker_client')
    def test_backup_redis(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_container = MagicMock()
        mock_container.status = "running"
        mock_container.exec_run.return_value = MagicMock(exit_code=0)

        # Mock get_archive for dump.rdb
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            info = tarfile.TarInfo(name="dump.rdb")
            data = b"REDIS RDB CONTENT"
            info.size = len(data)
            tar.addfile(tarinfo=info, fileobj=io.BytesIO(data))
        tar_stream.seek(0)

        mock_container.get_archive.return_value = ([tar_stream.read()], {'name': 'dump.rdb'})
        mock_client.containers.get.return_value = mock_container

        backup_path = backup_database(self.project, "redis")

        self.assertTrue(os.path.exists(backup_path))
        with open(backup_path, "rb") as f:
            self.assertEqual(f.read(), b"REDIS RDB CONTENT")

        os.remove(backup_path)

    @patch('projects.dr.provision_database')
    @patch('projects.dr.get_docker_client')
    def test_restore_postgres(self, mock_get_client, mock_provision):
        mock_container = MagicMock()
        mock_container.attrs = {'Config': {'Env': ['POSTGRES_PASSWORD=secret']}}
        mock_container.exec_run.return_value = MagicMock(exit_code=0)
        mock_provision.return_value = mock_container

        # Create a dummy backup file
        backup_path = "test_backup.sql"
        with open(backup_path, "wb") as f:
            f.write(b"RESTORE CONTENT")

        restore_database(self.project, "postgres", backup_path)

        mock_container.put_archive.assert_called_once()
        mock_container.exec_run.assert_called_once()

        os.remove(backup_path)

    @patch('projects.dr.get_docker_client')
    @patch('projects.dr.provision_database')
    def test_restore_redis(self, mock_provision, mock_get_client):
        mock_get_client.return_value = MagicMock()
        mock_container = MagicMock()
        mock_provision.return_value = mock_container

        backup_path = "test_backup.rdb"
        with open(backup_path, "wb") as f:
            f.write(b"RESTORE CONTENT")

        restore_database(self.project, "redis", backup_path)

        mock_container.stop.assert_called_once()
        mock_container.put_archive.assert_called_once()
        mock_container.start.assert_called_once()

        os.remove(backup_path)

    @patch('projects.dr.provision_database')
    @patch('projects.dr.backup_database')
    @patch('projects.dr.restore_database')
    @patch('projects.dr.get_docker_client')
    @patch('projects.dr.get_db_container')
    def test_dr_validation_unit(self, mock_get_db_container, mock_get_client, mock_restore, mock_backup, mock_provision):
        mock_container = MagicMock()
        mock_container.name = "test-container"
        mock_container.exec_run.return_value = MagicMock(output=b"khamal_is_awesome")
        mock_provision.return_value = mock_container
        mock_get_db_container.return_value = mock_container
        mock_backup.return_value = "/tmp/backup.sql"

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        res = run_dr_validation(self.project, "postgres")

        self.assertTrue(res)
        mock_provision.assert_called()
        mock_backup.assert_called_with(self.project, "postgres")
        mock_container.remove.assert_called_once()
        mock_restore.assert_called_with(self.project, "postgres", "/tmp/backup.sql")
