from django.test import TestCase
from projects.models import Project
from django.contrib.auth import get_user_model
from .models import LocalSource

User = get_user_model()

class LocalSourceModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser_local", password="password")
        self.project = Project.objects.create(name="LocalProject", owner=self.user)

    def test_local_source_creation(self):
        ls = LocalSource.objects.create(
            project=self.project,
            host_path="/tmp/host",
            container_path="/tmp/container"
        )
        self.assertEqual(ls.host_path, "/tmp/host")
        self.assertEqual(ls.container_path, "/tmp/container")
        self.assertEqual(str(ls), f"Local source for {self.project.name} (/tmp/host)")
