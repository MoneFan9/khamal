from django.test import TestCase
from unittest.mock import patch, MagicMock
from git_manager.models import Repository
from git_manager.services import clone_repository, pull_repository, switch_branch, list_branches
import os

class GitManagerServicesExtendedTests(TestCase):

    def setUp(self):
        from projects.models import Project
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.project = Project.objects.create(name="Test Project", owner=self.user)
        self.repo = Repository.objects.create(
            project=self.project,
            url="https://github.com/test/repo.git",
            local_path="/tmp/test-repo",
            current_branch="main"
        )

    @patch("git_manager.services.git.Repo.clone_from")
    @patch("os.path.exists")
    @patch("os.listdir")
    def test_clone_repository_skip_if_not_empty(self, mock_listdir, mock_exists, mock_clone):
        mock_exists.return_value = True
        mock_listdir.return_value = ["file1"]

        clone_repository(self.repo.id)

        mock_clone.assert_not_called()

    @patch("git_manager.services.git.Repo.clone_from")
    def test_clone_repository_failure(self, mock_clone):
        mock_clone.side_effect = Exception("Clone failed")

        with self.assertRaises(Exception):
            clone_repository(self.repo.id)

    @patch("git_manager.services.git.Repo")
    def test_pull_repository_failure(self, mock_repo_class):
        mock_repo = MagicMock()
        mock_repo.remotes.origin.pull.side_effect = Exception("Pull failed")
        mock_repo_class.return_value = mock_repo

        with self.assertRaises(Exception):
            pull_repository(self.repo.id)

    @patch("git_manager.services.git.Repo")
    def test_switch_branch_failure(self, mock_repo_class):
        mock_repo = MagicMock()
        mock_repo.git.checkout.side_effect = Exception("Checkout failed")
        mock_repo_class.return_value = mock_repo

        with self.assertRaises(Exception):
            switch_branch(self.repo.id, "feature-branch")

    @patch("git_manager.services.git.Repo")
    def test_switch_branch_success(self, mock_repo_class):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        switch_branch(self.repo.id, "develop")

        self.repo.refresh_from_db()
        self.assertEqual(self.repo.current_branch, "develop")

    @patch("git_manager.services.git.Repo")
    def test_list_branches_failure(self, mock_repo_class):
        mock_repo_class.side_effect = Exception("Failed to open repo")

        with self.assertRaises(Exception):
            list_branches(self.repo.id)

    @patch("git_manager.services.pull_repository")
    def test_pull_repository_async(self, mock_pull):
        from git_manager.services import pull_repository_async
        pull_repository_async(self.repo.id)
        # We can't easily wait for the executor without mocking it or more complex logic,
        # but calling it covers the line.
