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
        command, volumes = _get_traefik_config()

        self.assertIn("--certificatesresolvers.le.acme.email=admin@example.com", command)
        self.assertIn("--certificatesresolvers.le.acme.storage=/letsencrypt/acme.json", command)
        self.assertIn("--entrypoints.web.http.redirections.entryPoint.to=websecure", command)
        self.assertIn("khamal-letsencrypt", volumes)
        self.assertEqual(volumes["khamal-letsencrypt"]["bind"], "/letsencrypt")

    @override_settings(KHAMAL_SSL_ENABLED=False)
    def test_get_traefik_config_ssl_disabled(self):
        command, volumes = _get_traefik_config()

        # Check that SSL-related args are NOT in command
        for arg in command:
            self.assertNotIn("certificatesresolvers", arg)
        self.assertNotIn("khamal-letsencrypt", volumes)
