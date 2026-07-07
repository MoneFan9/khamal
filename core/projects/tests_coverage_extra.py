import pytest
from unittest.mock import patch, MagicMock
from django.conf import settings
from projects.nixpacks import build_image, NixpacksError
from projects.services import _get_traefik_config

@pytest.mark.asyncio
async def test_nixpacks_unexpected_error_coverage():
    """Covers lines 111-113 in nixpacks.py (Unexpected error handling)."""
    with patch("projects.nixpacks.asyncio.create_subprocess_exec", side_effect=Exception("Unexpected boom")):
        with pytest.raises(NixpacksError, match="Unexpected error"):
            await build_image("some/path", "test-image")

def test_get_traefik_config_ssl_enabled_coverage():
    """Covers lines 25-48 in services.py (Traefik config with SSL enabled)."""
    with patch("django.conf.settings.KHAMAL_SSL_ENABLED", True), \
         patch("django.conf.settings.KHAMAL_ACME_EMAIL", "test@example.com"), \
         patch("django.conf.settings.KHAMAL_ACME_STORAGE", "/letsencrypt/acme.json"), \
         patch("django.conf.settings.KHAMAL_ACME_CA_SERVER", "https://acme-v02.api.letsencrypt.org/directory"):

        command, volumes = _get_traefik_config()

        assert "--certificatesresolvers.le.acme.email=test@example.com" in command
        assert "khamal-letsencrypt" in volumes
        assert volumes["khamal-letsencrypt"]["bind"] == "/letsencrypt"
