from io import StringIO
from django.core.management import call_command
from django.test import SimpleTestCase
from unittest.mock import patch

class SetupTraefikCommandTests(SimpleTestCase):

    @patch("projects.management.commands.setup_traefik.ensure_global_proxy")
    def test_setup_traefik_success(self, mock_ensure):
        out = StringIO()
        call_command("setup_traefik", stdout=out)
        self.assertIn("Setting up global Traefik proxy...", out.getvalue())
        self.assertIn("Global Traefik proxy is set up and running.", out.getvalue())
        mock_ensure.assert_called_once()

    @patch("projects.management.commands.setup_traefik.ensure_global_proxy")
    def test_setup_traefik_failure(self, mock_ensure):
        mock_ensure.side_effect = Exception("Docker error")
        out = StringIO()
        call_command("setup_traefik", stdout=out)
        self.assertIn("Failed to set up Traefik proxy: Docker error", out.getvalue())
