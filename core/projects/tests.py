from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Project, Deployment

User = get_user_model()

class ProjectModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")

    def test_project_creation(self):
        project = Project.objects.create(
            name="Test Project",
            description="Test Description",
            owner=self.user
        )
        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.owner, self.user)
        self.assertEqual(str(project), "Test Project")

class DeploymentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser2", password="password")
        self.project = Project.objects.create(
            name="Test Project 2",
            owner=self.user
        )

    def test_deployment_creation(self):
        deployment = Deployment.objects.create(
            project=self.project,
            status=Deployment.Status.PENDING
        )
        self.assertEqual(deployment.project, self.project)
        self.assertEqual(deployment.status, Deployment.Status.PENDING)
        self.assertIn("Test Project 2", str(deployment))
