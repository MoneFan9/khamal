import pytest
from unittest.mock import MagicMock, patch
from projects.services import _get_traefik_config
from django.conf import settings

def test_get_traefik_config_no_ssl(settings):
    settings.KHAMAL_SSL_ENABLED = False
    command, volumes = _get_traefik_config()

    assert "--entrypoints.web.address=:80" in command
    assert "--entrypoints.websecure.address=:443" in command
    assert "/var/run/docker.sock" in volumes
    assert "khamal-letsencrypt" not in volumes
    assert "--certificatesresolvers.le.acme.email=" not in "".join(command)

def test_get_traefik_config_with_ssl(settings):
    settings.KHAMAL_SSL_ENABLED = True
    settings.KHAMAL_ACME_EMAIL = "test@example.com"
    settings.KHAMAL_ACME_STORAGE = "/tmp/acme.json"
    settings.KHAMAL_ACME_CA_SERVER = "https://acme.staging.com"

    command, volumes = _get_traefik_config()

    assert "--certificatesresolvers.le.acme.email=test@example.com" in command
    assert "--certificatesresolvers.le.acme.storage=/tmp/acme.json" in command
    assert "--certificatesresolvers.le.acme.caserver=https://acme.staging.com" in command
    assert "--entrypoints.web.http.redirections.entryPoint.to=websecure" in command
    assert "khamal-letsencrypt" in volumes
    assert volumes["khamal-letsencrypt"]["bind"] == "/letsencrypt"
