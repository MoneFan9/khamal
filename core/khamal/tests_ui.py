import pytest
from django.urls import reverse
from django.apps import apps

@pytest.mark.django_db
def test_white_label_css_injection_order(client):
    """
    Test that the White Label custom CSS is injected after the base styles.
    """
    if not apps.is_installed('pro.white_label'):
        pytest.skip("pro.white_label not installed")

    WhiteLabelConfiguration = apps.get_model('white_label', 'WhiteLabelConfiguration')
    custom_css = ".custom-class { color: red; }"
    WhiteLabelConfiguration.objects.create(
        name="Test Config",
        custom_css=custom_css,
        is_active=True
    )

    response = client.get("/")
    html = response.content.decode()

    # Check that Tailwind CDN is before custom CSS
    tailwind_index = html.find("cdn.tailwindcss.com")
    custom_css_index = html.find(custom_css)

    assert tailwind_index != -1
    assert custom_css_index != -1
    assert tailwind_index < custom_css_index
    assert '<style id="white-label-css">' in html

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
