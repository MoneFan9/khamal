from django.test import TestCase, override_settings
from projects.services import _get_traefik_config

class TraefikSSLTests(TestCase):

    @override_settings(
        KHAMAL_SSL_ENABLED=True,
        KHAMAL_ACME_EMAIL="admin@example.com",
        KHAMAL_ACME_STORAGE="/letsencrypt/acme.json",
        KHAMAL_ACME_CA_SERVER="https://acme-v02.api.letsencrypt.org/directory"
    )
    def test_get_traefik_config_ssl_enabled(self):
        """
        Covers the SSL configuration branches in _get_traefik_config.
        """
        command, volumes = _get_traefik_config()

        assert "--certificatesresolvers.le.acme.email=admin@example.com" in command
        assert "--certificatesresolvers.le.acme.storage=/letsencrypt/acme.json" in command
        assert "--certificatesresolvers.le.acme.tlschallenge=true" in command
        assert "--entrypoints.web.http.redirections.entryPoint.to=websecure" in command

        assert "khamal-letsencrypt" in volumes
        assert volumes["khamal-letsencrypt"]["bind"] == "/letsencrypt"

    @override_settings(KHAMAL_SSL_ENABLED=False)
    def test_get_traefik_config_ssl_disabled(self):
        """
        Covers the SSL disabled branch in _get_traefik_config.
        """
        command, volumes = _get_traefik_config()

        # Check that SSL-related args are NOT in the command
        assert not any("certificatesresolvers" in arg for arg in command)
        assert "khamal-letsencrypt" not in volumes
