from django.test import TestCase
from django.core.management import call_command
from unittest.mock import patch, MagicMock
from .models import Project, DatabaseInstance
from django.contrib.auth import get_user_model
import docker
import os
import io
import tarfile

User = get_user_model()

class DRManagerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dr_user", password="password")
        self.project = Project.objects.create(name="DRProject", owner=self.user)
        self.db_inst = DatabaseInstance.objects.create(
            project=self.project,
            engine="postgres",
            db_name="khamal",
            db_user="khamal",
            db_password="securepassword"
        )
        self.backup_file = "test_backup.sql"

    def tearDown(self):
        if os.path.exists(self.backup_file):
            os.remove(self.backup_file)
        if os.path.exists("test_redis_backup.tar"):
            os.remove("test_redis_backup.tar")

    @patch('projects.management.commands.dr_manager.get_docker_client')
    def test_backup_postgres(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_container = MagicMock()
        mock_container.id = "cont_id"
        mock_client.containers.get.return_value = mock_container

        mock_client.api.exec_create.return_value = {"Id": "exec_123"}
        # demux=True returns (stdout, stderr) tuples
        mock_client.api.exec_start.return_value = [(b"DUMP CONTENT", None)]
        mock_client.api.exec_inspect.return_value = {"ExitCode": 0}

        call_command("dr_manager", "backup", "--project-id", self.project.id, "--engine", "postgres", "--file", self.backup_file)

        mock_client.api.exec_create.assert_called_once()
        self.assertTrue(os.path.exists(self.backup_file))
        with open(self.backup_file, "rb") as f:
            self.assertEqual(f.read(), b"DUMP CONTENT")

    @patch('projects.management.commands.dr_manager.get_docker_client')
    @patch('projects.management.commands.dr_manager.provision_database')
    def test_restore_postgres(self, mock_provision, mock_get_client):
        with open(self.backup_file, "wb") as f:
            f.write(b"DUMP CONTENT")

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_container = MagicMock()
        mock_container.id = "cont_id"
        mock_provision.return_value = mock_container

        mock_container.exec_run.return_value = MagicMock(exit_code=0, output=b"RESTORE SUCCESS")

        call_command("dr_manager", "restore", "--project-id", self.project.id, "--engine", "postgres", "--file", self.backup_file)

        mock_client.api.put_archive.assert_called_once()
        mock_container.exec_run.assert_called_once()
        self.assertIn("psql", mock_container.exec_run.call_args[0][0])

    @patch('projects.management.commands.dr_manager.get_docker_client')
    def test_backup_redis(self, mock_get_client):
        # Create redis db instance
        DatabaseInstance.objects.create(
            project=self.project,
            engine="redis",
            db_password="redispassword"
        )
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container

        mock_container.exec_run.return_value = MagicMock(exit_code=0, output=b"OK")

        # Mock get_archive stream
        def mock_get_archive_stream(path):
            yield b"TAR CONTENT"

        mock_container.get_archive.return_value = (mock_get_archive_stream("/data/dump.rdb"), {})

        call_command("dr_manager", "backup", "--project-id", self.project.id, "--engine", "redis", "--file", "test_redis_backup.tar")

        self.assertTrue(os.path.exists("test_redis_backup.tar"))
        with open("test_redis_backup.tar", "rb") as f:
            self.assertEqual(f.read(), b"TAR CONTENT")

    @patch('projects.management.commands.dr_manager.get_docker_client')
    @patch('projects.management.commands.dr_manager.provision_database')
    def test_restore_redis(self, mock_provision, mock_get_client):
        redis_backup = "test_redis_backup.tar"
        with open(redis_backup, "wb") as f:
            f.write(b"TAR CONTENT")

        # Update db_inst for redis
        self.db_inst.engine = "redis"
        self.db_inst.save()

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_container = MagicMock()
        mock_container.id = "cont_id"
        mock_provision.return_value = mock_container

        call_command("dr_manager", "restore", "--project-id", self.project.id, "--engine", "redis", "--file", redis_backup)

        mock_container.stop.assert_called_once()
        mock_client.api.put_archive.assert_called_once()
        args, kwargs = mock_client.api.put_archive.call_args
        self.assertEqual(args[1], "/data/")
        mock_container.start.assert_called_once()
