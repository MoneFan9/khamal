from django.test import TestCase
from django.contrib.auth import get_user_model
from projects.models import Project
from .models import Repository
from .services import clone_repository, switch_branch
import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock

User = get_user_model()

class GitManagerExtendedTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser_ext", password="password")
        self.project = Project.objects.create(name="Test Project Ext", owner=self.user)
        self.temp_dir = tempfile.mkdtemp()
        self.repository = Repository.objects.create(
            project=self.project,
            url="https://github.com/example/repo.git",
            local_path=os.path.join(self.temp_dir, "repo"),
            current_branch="main"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch('git_manager.services.git.Repo')
    @patch('git_manager.services.logger')
    def test_clone_repository_path_not_empty(self, mock_logger, mock_repo):
        # Create a non-empty directory
        os.makedirs(self.repository.local_path, exist_ok=True)
        with open(os.path.join(self.repository.local_path, "file.txt"), "w") as f:
            f.write("content")

        clone_repository(self.repository.id)

        # Verify it skipped clone
        mock_repo.clone_from.assert_not_called()
        mock_logger.warning.assert_called_with(f"Path {self.repository.local_path} is not empty. Skipping clone.")

    @patch('git_manager.services.git.Repo')
    def test_switch_branch_success(self, mock_repo_class):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        switch_branch(self.repository.id, "develop")

        # Verify branch switch
        mock_repo.remotes.origin.fetch.assert_called_once()
        mock_repo.git.checkout.assert_called_with("develop")

        self.repository.refresh_from_db()
        self.assertEqual(self.repository.current_branch, "develop")
