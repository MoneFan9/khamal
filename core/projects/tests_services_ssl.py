from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.conf import settings
from projects.services import ensure_global_proxy
import docker

class ServicesSSLTests(TestCase):

    @patch("projects.services.get_docker_client")
    @patch("projects.services.settings")
    def test_ensure_global_proxy_ssl_enabled(self, mock_settings, mock_get_client):
        mock_settings.KHAMAL_SSL_ENABLED = True
        mock_settings.KHAMAL_ACME_EMAIL = "test@example.com"
        mock_settings.KHAMAL_ACME_STORAGE = "/tmp/acme.json"
        mock_settings.KHAMAL_ACME_CA_SERVER = "https://acme-staging.org"

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock network exists
        mock_client.networks.get.return_value = MagicMock()

        # Mock container not found (so it tries to run it)
        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")

        ensure_global_proxy()

        # Verify containers.run was called with SSL args
        self.assertTrue(mock_client.containers.run.called)
        _, kwargs = mock_client.containers.run.call_args
        command = kwargs.get("command", [])
        self.assertIn("--certificatesresolvers.le.acme.email=test@example.com", command)
        self.assertIn("--certificatesresolvers.le.acme.storage=/tmp/acme.json", command)
