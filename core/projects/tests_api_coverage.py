import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from projects.models import Project, Deployment

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="password")

@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="otheruser", password="password")

@pytest.mark.django_db
class TestProjectAPI:
    def test_list_projects_authenticated(self, api_client, user):
        api_client.force_authenticate(user=user)
        Project.objects.create(name="Project 1", owner=user)

        response = api_client.get("/api/projects/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Project 1"

    def test_list_projects_unauthenticated(self, api_client):
        response = api_client.get("/api/projects/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_project(self, api_client, user):
        api_client.force_authenticate(user=user)
        data = {"name": "New Project"}
        response = api_client.post("/api/projects/", data)

        assert response.status_code == status.HTTP_201_CREATED
        assert Project.objects.count() == 1
        assert Project.objects.first().owner == user

@pytest.mark.django_db
class TestDeploymentAPI:
    def test_list_deployments_only_owner(self, api_client, user, other_user):
        proj_user = Project.objects.create(name="User Project", owner=user)
        proj_other = Project.objects.create(name="Other Project", owner=other_user)

        dep_user = Deployment.objects.create(project=proj_user)
        dep_other = Deployment.objects.create(project=proj_other)

        api_client.force_authenticate(user=user)
        response = api_client.get("/api/projects/deployments/")

        assert response.status_code == status.HTTP_200_OK
        # The API filters by project__owner=self.request.user
        assert len(response.data) == 1
