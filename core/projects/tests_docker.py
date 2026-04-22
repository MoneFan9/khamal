from django.test import TestCase
from django.conf import settings
from .docker_client import get_docker_client
from unittest.mock import patch

class DockerClientTest(TestCase):
    @patch('docker.DockerClient')
    def test_get_docker_client_uses_settings_url(self, mock_docker_client):
        get_docker_client()
        mock_docker_client.assert_called_once_with(base_url=settings.DOCKER_URL)
