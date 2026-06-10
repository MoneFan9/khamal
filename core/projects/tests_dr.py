from django.test import TestCase
from unittest.mock import patch, MagicMock
from projects.models import Project, Backup, DatabaseInstance
from projects.services import perform_database_backup, restore_database_backup, provision_database
from django.contrib.auth import get_user_model
import os
import tarfile
import io

User = get_user_model()

class DisasterRecoveryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dr_user", password="password")
        self.project = Project.objects.create(name="DR Project", owner=self.user)

    @patch('projects.services.get_docker_client')
    @patch('projects.services.ensure_project_network')
    @patch('projects.services._wait_for_healthy')
    def test_provision_database_persists_credentials(self, mock_wait, mock_ensure_net, mock_get_client):
        mock_wait.return_value = True
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        import docker
        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found") # Force creation

        provision_database(self.project, "postgres")

        db_inst = DatabaseInstance.objects.get(project=self.project, engine="postgres")
        self.assertTrue(db_inst.db_password)
        self.assertEqual(db_inst.db_name, "khamal")

    @patch('projects.services.get_docker_client')
    def test_perform_database_backup_postgres(self, mock_get_client):
        db_inst = DatabaseInstance.objects.create(
            project=self.project,
            engine="postgres",
            db_password="secret_password"
        )

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container

        # Mock exec_run with socket=True
        mock_res = MagicMock()
        mock_res.output = MagicMock() # This will be the "socket"
        mock_container.exec_run.return_value = mock_res

        # We need to mock docker_socket.frames_iter
        with patch('docker.utils.socket.frames_iter') as mock_frames:
            mock_frames.return_value = [(None, b"DUMMY SQL CONTENT")]

            file_path = perform_database_backup(self.project, "postgres")

        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "rb") as f:
            self.assertEqual(f.read(), b"DUMMY SQL CONTENT")

        backup_obj = Backup.objects.get(project=self.project, engine="postgres")
        self.assertEqual(backup_obj.status, Backup.Status.COMPLETED)

    @patch('projects.services.get_docker_client')
    def test_perform_database_backup_redis(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container

        mock_container.exec_run.side_effect = [
            (0, b"Background saving started"),
            (0, b"rdb_bgsave_in_progress:0")
        ]

        # Mock get_archive for Redis dump.rdb
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            content = b"DUMMY RDB CONTENT"
            tarinfo = tarfile.TarInfo(name="dump.rdb")
            tarinfo.size = len(content)
            tar.addfile(tarinfo, io.BytesIO(content))

        # It expects an iterator
        mock_container.get_archive.return_value = (iter([tar_stream.getvalue()]), {})

        file_path = perform_database_backup(self.project, "redis")

        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "rb") as f:
            self.assertEqual(f.read(), b"DUMMY RDB CONTENT")

    @patch('projects.services.provision_database')
    @patch('projects.services.get_docker_client')
    def test_restore_database_backup_postgres(self, mock_get_client, mock_provision):
        db_inst = DatabaseInstance.objects.create(
            project=self.project,
            engine="postgres",
            db_password="secret_password"
        )

        mock_container = MagicMock()
        mock_provision.return_value = mock_container
        mock_container.exec_run.return_value = (0, b"SUCCESS")

        # Create a dummy backup file
        backup_path = "/tmp/dummy_backup.sql"
        with open(backup_path, "wb") as f:
            f.write(b"RESTORE ME")

        backup = Backup.objects.create(
            project=self.project,
            engine="postgres",
            file_path=backup_path,
            status=Backup.Status.COMPLETED
        )

        restore_database_backup(backup)

        # Check if put_archive was called (uploading restore.sql)
        mock_container.put_archive.assert_called()
        # Check if psql was executed
        self.assertIn("psql", mock_container.exec_run.call_args_list[-1][0][0])
