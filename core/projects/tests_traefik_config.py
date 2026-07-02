from django.test import TestCase, override_settings
from django.conf import settings
from .services import _get_traefik_config, PROXY_NETWORK_NAME

class TraefikConfigTests(TestCase):
    @override_settings(KHAMAL_SSL_ENABLED=False)
    def test_get_traefik_config_no_ssl(self):
        command, volumes = _get_traefik_config()
        self.assertIn("--providers.docker=true", command)
        self.assertIn(f"--providers.docker.network={PROXY_NETWORK_NAME}", command)
        self.assertNotIn("--certificatesresolvers.le.acme.email=test@example.com", command)
        self.assertIn("/var/run/docker.sock", volumes)
        self.assertNotIn("khamal-letsencrypt", volumes)

    @override_settings(
        KHAMAL_SSL_ENABLED=True,
        KHAMAL_ACME_EMAIL="test@example.com",
        KHAMAL_ACME_STORAGE="/letsencrypt/acme.json",
        KHAMAL_ACME_CA_SERVER="https://acme-v02.api.letsencrypt.org/directory"
    )
    def test_get_traefik_config_with_ssl(self):
        command, volumes = _get_traefik_config()
        self.assertIn("--certificatesresolvers.le.acme.email=test@example.com", command)
        self.assertIn("--certificatesresolvers.le.acme.storage=/letsencrypt/acme.json", command)
        self.assertIn("khamal-letsencrypt", volumes)
        self.assertEqual(volumes["khamal-letsencrypt"]["bind"], "/letsencrypt")
