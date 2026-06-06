import pytest
from unittest.mock import MagicMock, patch
from django.conf import settings
from projects.services import _get_traefik_config

@pytest.mark.django_db
def test_get_traefik_config_ssl_enabled():
    """
    Test Traefik configuration generation when SSL is enabled.
    Covers lines 25-48 of core/projects/services.py.
    """
    with patch("django.conf.settings.KHAMAL_SSL_ENABLED", True), \
         patch("django.conf.settings.KHAMAL_ACME_EMAIL", "admin@example.com"), \
         patch("django.conf.settings.KHAMAL_ACME_STORAGE", "/letsencrypt/acme.json"), \
         patch("django.conf.settings.KHAMAL_ACME_CA_SERVER", "https://acme-v02.api.letsencrypt.org/directory"):

        command, volumes = _get_traefik_config()

        # Check SSL specific commands
        assert "--certificatesresolvers.le.acme.email=admin@example.com" in command
        assert "--certificatesresolvers.le.acme.storage=/letsencrypt/acme.json" in command
        assert "--certificatesresolvers.le.acme.tlschallenge=true" in command
        assert "--certificatesresolvers.le.acme.caserver=https://acme-v02.api.letsencrypt.org/directory" in command
        assert "--entrypoints.web.http.redirections.entryPoint.to=websecure" in command
        assert "--entrypoints.web.http.redirections.entryPoint.scheme=https" in command

        # Check volumes
        assert "khamal-letsencrypt" in volumes
        assert volumes["khamal-letsencrypt"] == {"bind": "/letsencrypt", "mode": "rw"}

@pytest.mark.django_db
def test_get_traefik_config_ssl_disabled():
    """
    Test Traefik configuration generation when SSL is disabled.
    """
    with patch("django.conf.settings.KHAMAL_SSL_ENABLED", False):
        command, volumes = _get_traefik_config()

        # SSL specific commands should NOT be present
        assert not any("--certificatesresolvers" in cmd for cmd in command)
        assert not any("redirections" in cmd for cmd in command)

        # khamal-letsencrypt volume should NOT be present
        assert "khamal-letsencrypt" not in volumes
