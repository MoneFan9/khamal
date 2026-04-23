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

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

class ProjectAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="apiuser", password="password")
        self.client.force_authenticate(user=self.user)
        self.url = reverse('project-list-create')

    def test_create_project_api(self):
        data = {'name': 'New API Project', 'description': 'Created via API'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Project.objects.get().name, 'New API Project')
        self.assertEqual(Project.objects.get().owner, self.user)

    def test_list_projects_api(self):
        Project.objects.create(name='Project 1', owner=self.user)
        Project.objects.create(name='Project 2', owner=self.user)

        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_project_unauthenticated(self):
        self.client.force_authenticate(user=None)
        data = {'name': 'Unauthorized Project'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class ProjectDomainTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="domainuser", password="password")

    def test_automatic_domain_generation(self):
        project = Project.objects.create(
            name="My Awesome Project",
            owner=self.user
        )
        # Should be slugified name + .khamal.local
        self.assertEqual(project.domain, "my-awesome-project.khamal.local")

    def test_manual_domain_preserved(self):
        project = Project.objects.create(
            name="Custom Domain Project",
            domain="custom.example.com",
            owner=self.user
        )
        self.assertEqual(project.domain, "custom.example.com")
