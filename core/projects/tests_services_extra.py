import pytest
from unittest.mock import patch, MagicMock
from django.conf import settings
from projects.services import _get_traefik_config, PROXY_NETWORK_NAME

@pytest.mark.django_db
class TestServicesExtra:
    def test_get_traefik_config_ssl_disabled(self):
        with patch.object(settings, "KHAMAL_SSL_ENABLED", False):
            command, volumes = _get_traefik_config()
            assert "--entrypoints.web.address=:80" in command
            assert "--entrypoints.websecure.address=:443" in command
            assert f"--providers.docker.network={PROXY_NETWORK_NAME}" in command
            assert "/var/run/docker.sock" in volumes
            assert "khamal-letsencrypt" not in volumes
            assert not any("acme" in arg for arg in command)

    def test_get_traefik_config_ssl_enabled(self):
        with patch.object(settings, "KHAMAL_SSL_ENABLED", True), \
             patch.object(settings, "KHAMAL_ACME_EMAIL", "test@example.com"), \
             patch.object(settings, "KHAMAL_ACME_STORAGE", "/letsencrypt/acme.json"), \
             patch.object(settings, "KHAMAL_ACME_CA_SERVER", "https://acme-v02.api.letsencrypt.org/directory"):
            command, volumes = _get_traefik_config()
            assert "--certificatesresolvers.le.acme.email=test@example.com" in command
            assert "--certificatesresolvers.le.acme.storage=/letsencrypt/acme.json" in command
            assert "--certificatesresolvers.le.acme.tlschallenge=true" in command
            assert "khamal-letsencrypt" in volumes
            assert volumes["khamal-letsencrypt"] == {"bind": "/letsencrypt", "mode": "rw"}
