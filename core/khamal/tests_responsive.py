import pytest
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_responsive_classes_present():
    """
    Vérifie que les classes Tailwind CSS pour la réactivité (responsive)
    sont présentes dans le template de base.
    """
    factory = RequestFactory()
    request = factory.get('/')
    user = User.objects.create_user(username='testuser')
    request.user = user

    # Simuler le contexte nécessaire
    context = {
        'user': user,
        'is_pro_loaded': False,
        'white_label_config': None
    }

    html = render_to_string('base.html', context, request=request)

    # Vérifier la présence des classes de visibilité responsive
    assert 'sm:hidden' in html       # Bouton menu mobile
    assert 'id="mobile-menu"' in html # Conteneur menu mobile

@pytest.mark.django_db
def test_modern_ui_elements_present():
    """
    Vérifie que les nouveaux éléments d'interface moderne sont présents.
    """
    factory = RequestFactory()
    request = factory.get('/')
    user = User.objects.create_user(username='testuser2')
    request.user = user

    context = {
        'user': user,
        'is_pro_loaded': True,
    }

    html = render_to_string('base.html', context, request=request)

    assert 'transition-all' in html
    assert 'duration-500' in html
    assert 'rounded-full' in html # Pour les badges pro
    assert 'shadow-2xl' in html    # Pour les boutons

@pytest.mark.django_db
def test_dashboard_modern_elements():
    """
    Vérifie que le tableau de bord contient les nouveaux éléments modernes.
    """
    from django.utils import timezone
    factory = RequestFactory()
    request = factory.get('/')
    user = User.objects.create_user(username='testuser3')
    request.user = user

    class MockDeployment:
        def __init__(self, status):
            self.status = status
            self.id = 1

    class MockDeployments:
        def __init__(self, first):
            self.first = first
        def all(self):
            return [self.first] if self.first else []

    class MockProject:
        def __init__(self, name, domain, status):
            self.name = name
            self.domain = domain
            self.deployments = MockDeployments(MockDeployment(status))
            self.updated_at = timezone.now()
            self.description = "Test description"
            self.id = 1

    context = {
        'user': user,
        'projects': [MockProject('Test Project', 'test.com', 'RUNNING')]
    }

    html = render_to_string('dashboard.html', context, request=request)

    assert 'rounded-[2.5rem]' in html
    assert 'animate-ping' in html
    assert 'hover:-translate-y-2' in html
