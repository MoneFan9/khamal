from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Project, Deployment
from .serializers import ProjectSerializer
from local.models import LocalSource

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

class ProjectSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="seruser", password="password")

    def test_create_project_with_local_source(self):
        import os
        from django.conf import settings
        valid_host_path = os.path.abspath(os.path.join(str(settings.BASE_DIR), "test_path"))
        data = {
            "name": "Test Project",
            "local_source": {
                "host_path": valid_host_path,
                "container_path": "/container/path"
            }
        }
        serializer = ProjectSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        project = serializer.save(owner=self.user)

        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.local_source.host_path, valid_host_path)

    def test_update_project_add_local_source(self):
        import os
        from django.conf import settings
        valid_host_path = os.path.abspath(os.path.join(str(settings.BASE_DIR), "new_host"))
        project = Project.objects.create(name="Old Name", owner=self.user)
        data = {
            "name": "New Name",
            "local_source": {
                "host_path": valid_host_path,
                "container_path": "/new/container"
            }
        }
        serializer = ProjectSerializer(instance=project, data=data)
        self.assertTrue(serializer.is_valid())
        project = serializer.save()

        self.assertEqual(project.name, "New Name")
        self.assertEqual(project.local_source.host_path, valid_host_path)

    def test_update_project_remove_local_source(self):
        project = Project.objects.create(name="Project", owner=self.user)
        LocalSource.objects.create(project=project, host_path="/h", container_path="/c")

        data = {
            "name": "Project",
            "local_source": None
        }
        serializer = ProjectSerializer(instance=project, data=data)
        self.assertTrue(serializer.is_valid())
        project = serializer.save()

        self.assertFalse(LocalSource.objects.filter(project=project).exists())

class ProjectViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="viewuser", password="password")
        self.other_user = User.objects.create_user(username="otheruser", password="password")
        self.project = Project.objects.create(name="View Project", owner=self.user)
        self.deployment = Deployment.objects.create(project=self.project)

    def test_deployment_logs_view_owner(self):
        self.client.login(username="viewuser", password="password")
        url = reverse('deployment-logs', kwargs={'deployment_id': self.deployment.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/deployment_logs.html')

    def test_deployment_logs_view_not_owner(self):
        self.client.login(username="otheruser", password="password")
        url = reverse('deployment-logs', kwargs={'deployment_id': self.deployment.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_deployment_logs_view_unauthenticated(self):
        url = reverse('deployment-logs', kwargs={'deployment_id': self.deployment.id})
        response = self.client.get(url)
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

class DeploymentAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="depuser", password="password")
        self.other_user = User.objects.create_user(username="otherdepuser", password="password")
        self.project = Project.objects.create(name="Project", owner=self.user)
        self.other_project = Project.objects.create(name="Other Project", owner=self.other_user)
        self.deployment = Deployment.objects.create(project=self.project)
        self.other_deployment = Deployment.objects.create(project=self.other_project)
        self.url = reverse('deployment-list-create')

    def test_list_deployments_filtered_by_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.deployment.id)

    def test_list_deployments_other_user(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.other_deployment.id)

class LocalSourceSerializerTest(TestCase):
    def test_validate_host_path_not_absolute(self):
        from rest_framework import serializers
        from .serializers import LocalSourceSerializer
        serializer = LocalSourceSerializer()
        with self.assertRaises(serializers.ValidationError) as cm:
            serializer.validate_host_path("not/absolute")
        self.assertIn("host_path must be an absolute path.", str(cm.exception))

    def test_validate_host_path_denied(self):
        from rest_framework import serializers
        from .serializers import LocalSourceSerializer
        serializer = LocalSourceSerializer()
        with self.assertRaises(serializers.ValidationError) as cm:
            # Assuming /etc is outside BASE_DIR
            serializer.validate_host_path("/etc/passwd")
        self.assertIn("denied", str(cm.exception))
