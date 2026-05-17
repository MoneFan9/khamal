import pytest
import os
from projects.models import Project, Database
from projects.backup_manager import BackupManager
from projects.services import provision_database
from django.contrib.auth import get_user_model
from django.core.management import call_command
from unittest.mock import MagicMock, patch

User = get_user_model()

@pytest.mark.django_db
class TestBackupRestore:
    @pytest.fixture
    def project(self, db):
        user = User.objects.create_user(username="testuser", password="password")
        return Project.objects.create(name="Test Project", owner=user)

    @patch("projects.backup_manager.get_docker_client")
    @patch("projects.services.get_docker_client")
    def test_postgres_backup_logic(self, mock_get_docker_services, mock_get_docker_backup, project):
        mock_client = MagicMock()
        mock_get_docker_backup.return_value = mock_client
        mock_get_docker_services.return_value = mock_client

        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container

        # Mock low-level API calls used in streaming backup
        mock_client.api.exec_create.return_value = {'Id': 'fake_exec_id'}
        mock_client.api.exec_start.return_value = [(b"dummy backup content", None)]
        mock_client.api.exec_inspect.return_value = {'ExitCode': 0}

        # We need a Database object
        db_obj = Database.objects.create(
            project=project,
            engine=Database.Engine.POSTGRES,
            db_name="khamal",
            db_user="khamal",
            db_password="password"
        )

        manager = BackupManager()
        backup_path = manager.backup(project, "postgres")

        assert os.path.exists(backup_path)
        assert "postgres" in backup_path

        with open(backup_path, "rb") as f:
            assert f.read() == b"dummy backup content"

        # Cleanup
        os.remove(backup_path)

    @patch("projects.backup_manager.get_docker_client")
    def test_redis_backup_logic(self, mock_get_docker, project):
        mock_client = MagicMock()
        mock_get_docker.return_value = mock_client

        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container
        mock_container.exec_run.return_value = MagicMock(exit_code=0)

        # Mock get_archive for Redis dump.rdb
        import tarfile
        import io
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            tarinfo = tarfile.TarInfo(name="dump.rdb")
            tarinfo.size = len(b"redis data")
            tar.addfile(tarinfo, io.BytesIO(b"redis data"))

        mock_container.get_archive.return_value = ([tar_stream.getvalue()], MagicMock())

        manager = BackupManager()
        backup_path = manager.backup(project, "redis")

        assert os.path.exists(backup_path)
        with open(backup_path, "rb") as f:
            assert f.read() == b"redis data"

        # Cleanup
        os.remove(backup_path)

    @patch("projects.backup_manager.get_docker_client")
    def test_postgres_restore_logic(self, mock_get_docker, project):
        mock_client = MagicMock()
        mock_get_docker.return_value = mock_client

        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container
        mock_container.exec_run.return_value = MagicMock(exit_code=0)

        db_obj = Database.objects.create(
            project=project,
            engine=Database.Engine.POSTGRES,
            db_name="khamal",
            db_user="khamal",
            db_password="password"
        )

        backup_path = "/tmp/fake_backup.sql"
        with open(backup_path, "wb") as f:
            f.write(b"fake sql")

        manager = BackupManager()
        manager.restore(project, "postgres", backup_path)

        assert mock_container.put_archive.called
        assert mock_container.exec_run.called

        # Cleanup
        os.remove(backup_path)
