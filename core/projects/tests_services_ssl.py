import pytest
from unittest.mock import patch, MagicMock
from django.conf import settings
from projects.services import _get_traefik_config

@pytest.mark.django_db
def test_get_traefik_config_ssl_disabled():
    with patch.object(settings, 'KHAMAL_SSL_ENABLED', False):
        command, volumes = _get_traefik_config()
        assert "--entrypoints.web.address=:80" in command
        # Verify no SSL related args
        assert "--entrypoints.websecure.address=:443" in command # It's always there in the base config
        assert not any("certificatesresolvers" in arg for arg in command)
        assert "/var/run/docker.sock" in volumes
        assert "khamal-letsencrypt" not in volumes

@pytest.mark.django_db
def test_get_traefik_config_ssl_enabled():
    with patch.object(settings, 'KHAMAL_SSL_ENABLED', True), \
         patch.object(settings, 'KHAMAL_ACME_EMAIL', 'test@example.com'), \
         patch.object(settings, 'KHAMAL_ACME_STORAGE', '/letsencrypt/acme.json'), \
         patch.object(settings, 'KHAMAL_ACME_CA_SERVER', 'https://acme-staging.api.letsencrypt.org/directory'):

        command, volumes = _get_traefik_config()
        assert "--entrypoints.websecure.address=:443" in command
        assert "--certificatesresolvers.le.acme.email=test@example.com" in command
        assert "khamal-letsencrypt" in volumes
        assert volumes["khamal-letsencrypt"]["bind"] == "/letsencrypt"
