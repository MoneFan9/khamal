import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_dashboard_displays_projects(client, admin_user):
    """
    Test that the dashboard correctly displays user projects.
    """
    from projects.models import Project
    Project.objects.create(name="Project A", owner=admin_user)
    Project.objects.create(name="Project B", owner=admin_user)

    client.force_login(admin_user)
    response = client.get("/")

    assert response.status_code == 200
    assert "Project A" in response.content.decode()
    assert "Project B" in response.content.decode()
    assert "Vos Projets" in response.content.decode()
