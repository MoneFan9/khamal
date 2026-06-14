from django.test import TestCase
from unittest.mock import patch, MagicMock
from .models import Project, DatabaseInstance, Backup
from .services import provision_database, backup_database, restore_database
from django.contrib.auth import get_user_model
import io
import docker

User = get_user_model()

class DisasterRecoveryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dr_user", password="password")
        self.project = Project.objects.create(name="DR Project", owner=self.user)

    @patch('projects.services.get_docker_client')
    @patch('projects.services.ensure_project_network')
    def test_provision_database_persists_credentials(self, mock_ensure_net, mock_get_client):
        mock_ensure_net.return_value = "net_dr"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")

        mock_container = MagicMock()
        mock_container.attrs = {"State": {"Health": {"Status": "healthy"}}}
        mock_client.containers.run.return_value = mock_container

        mock_net = MagicMock()
        mock_net.name = "net_dr_name"
        mock_client.networks.get.return_value = mock_net

        provision_database(self.project, "postgres")

        # Verify DatabaseInstance creation
        db_instance = DatabaseInstance.objects.get(project=self.project, engine="postgres")
        self.assertEqual(db_instance.container_name, f"khamal-db-postgres-{self.project.id}")
        self.assertTrue(len(db_instance.db_password) > 0)

        # Verify second call returns same instance/credentials
        password = db_instance.db_password
        provision_database(self.project, "postgres")
        db_instance.refresh_from_db()
        self.assertEqual(db_instance.db_password, password)

    @patch('projects.services.get_docker_client')
    def test_backup_database_postgres(self, mock_get_client):
        db_instance = DatabaseInstance.objects.create(
            project=self.project,
            engine="postgres",
            container_name="test-pg",
            db_password="secure"
        )

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock exec_create and exec_start for streaming
        mock_client.api.exec_create.return_value = {"Id": "exec_123"}
        # Mock frames_iter to return some "data"
        with patch('docker.utils.socket.frames_iter') as mock_frames:
            mock_frames.return_value = [(1, b"PG_DUMP_DATA")]

            backup = backup_database(db_instance)

            self.assertEqual(backup.status, Backup.Status.COMPLETED)
            self.assertIn("backup-postgres", backup.file_path)

            # Verify file content
            with open(backup.file_path, "rb") as f:
                self.assertEqual(f.read(), b"PG_DUMP_DATA")

    @patch('projects.services.get_docker_client')
    def test_backup_database_redis(self, mock_get_client):
        db_instance = DatabaseInstance.objects.create(
            project=self.project,
            engine="redis",
            container_name="test-redis",
            db_password="secure"
        )

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container

        # Mock redis info
        mock_container.exec_run.return_value.output = b"rdb_bgsave_in_progress:0"

        # Mock get_archive for Redis
        mock_container.get_archive.return_value = ([b"REDIS_DATA"], {"size": 10})

        backup = backup_database(db_instance)

        self.assertEqual(backup.status, Backup.Status.COMPLETED)
        with open(backup.file_path, "rb") as f:
            self.assertEqual(f.read(), b"REDIS_DATA")

    @patch('projects.services.get_docker_client')
    def test_restore_database_postgres(self, mock_get_client):
        db_instance = DatabaseInstance.objects.create(
            project=self.project,
            engine="postgres",
            container_name="test-pg-restore",
            db_password="secure"
        )

        # Create a dummy backup file
        import os
        backup_file = "/tmp/test_backup.dump"
        with open(backup_file, "wb") as f:
            f.write(b"RESTORE_DATA")

        backup = Backup.objects.create(
            db_instance=db_instance,
            status=Backup.Status.COMPLETED,
            file_path=backup_file
        )

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.api.exec_create.return_value = {"Id": "restore_123"}
        mock_client.api.exec_inspect.return_value = {"ExitCode": 0}

        # Mock socket
        mock_socket = MagicMock()
        mock_client.api.exec_start.return_value = mock_socket

        restore_database(db_instance, backup)

        mock_client.api.exec_create.assert_called_once()
        # Verify data was "sent" (simplified check as we mock the send logic)
        self.assertTrue(mock_socket.sendall.called or mock_socket.write.called)

    @patch('projects.services.get_docker_client')
    def test_restore_database_redis(self, mock_get_client):
        db_instance = DatabaseInstance.objects.create(
            project=self.project,
            engine="redis",
            container_name="test-redis-restore",
            db_password="secure"
        )

        backup_file = "/tmp/test_redis.rdb"
        with open(backup_file, "wb") as f:
            f.write(b"REDIS_RDB_DATA")

        backup = Backup.objects.create(
            db_instance=db_instance,
            status=Backup.Status.COMPLETED,
            file_path=backup_file
        )

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container

        restore_database(db_instance, backup)

        mock_container.stop.assert_called_once()
        mock_client.api.put_archive.assert_called_once()
        mock_container.start.assert_called_once()
