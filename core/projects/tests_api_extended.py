import pytest
from rest_framework.test import APIRequestFactory, force_authenticate
from projects.api_views import DeploymentListCreateAPIView
from projects.models import Project, Deployment
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_deployment_list_get_queryset():
    user1 = User.objects.create(username="user1")
    user2 = User.objects.create(username="user2")

    proj1 = Project.objects.create(name="proj1", owner=user1)
    proj2 = Project.objects.create(name="proj2", owner=user2)

    dep1 = Deployment.objects.create(project=proj1)
    dep2 = Deployment.objects.create(project=proj2)

    factory = APIRequestFactory()
    view = DeploymentListCreateAPIView()

    # Request from user1
    request = factory.get('/api/projects/deployments/')
    request.user = user1
    view.request = request

    qs = view.get_queryset()
    assert qs.count() == 1
    assert dep1 in qs
    assert dep2 not in qs
