import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from accounts.models import User
from projects.models import Project, Deployment

@pytest.mark.django_db
class TestProjectAPI:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.other_user = User.objects.create_user(username="otheruser", password="password")
        self.client.force_authenticate(user=self.user)

    def test_perform_create_sets_owner(self):
        url = reverse('project-list-create')
        data = {"name": "Test Project", "domain": "test.local"}
        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        project = Project.objects.get(name="Test Project")
        assert project.owner == self.user

    def test_deployment_queryset_filtering(self):
        p1 = Project.objects.create(name="My Project", owner=self.user)
        p2 = Project.objects.create(name="Other Project", owner=self.other_user)

        d1 = Deployment.objects.create(project=p1, status="RUNNING")
        d2 = Deployment.objects.create(project=p2, status="RUNNING")

        url = reverse('deployment-list-create')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['project'] == p1.id
