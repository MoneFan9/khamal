
import os
import django
from django.test import RequestFactory
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'khamal.settings.development')
django.setup()

from khamal.views import home
from projects.models import Project

def test_home_view_optimization():
    User = get_user_model()
    user = User.objects.get(username='admin')

    factory = RequestFactory()
    request = factory.get('/')
    request.user = user

    response = home(request)
    assert response.status_code == 200
    content = response.content.decode()

    # Check if projects are in the content
    assert "Site E-commerce" in content
    assert "API Analytics" in content
    assert "Blog Personnel" in content

    # Check if stats are correct
    # Site E-commerce (RUNNING), API Analytics (FAILED), Blog Personnel (None)
    assert "Total Projets" in content
    assert "3" in content # Total
    assert "1" in content # Running
    assert "1" in content # Failed

    print("Optimization test passed: Projects and stats correctly rendered.")

if __name__ == "__main__":
    test_home_view_optimization()
