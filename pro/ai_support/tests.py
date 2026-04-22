from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from pro.servers.models import Server
from .models import DiagnosticRequest

User = get_user_model()

class AISupportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Server with sufficient resources (LOCAL)
        self.local_server = Server.objects.create(
            name="Strong Server",
            hostname_or_ip="1.1.1.1",
            cpu_cores=8,
            memory_total=16 * 1024 * 1024 * 1024
        )

        # Server with low resources (CLOUD)
        self.cloud_server = Server.objects.create(
            name="Weak Server",
            hostname_or_ip="2.2.2.2",
            cpu_cores=2,
            memory_total=4 * 1024 * 1024 * 1024
        )

    def test_routing_to_local(self):
        url = "/api/pro/ai-support/diagnose/"
        data = {
            "server_id": self.local_server.id,
            "query": "High CPU usage"
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["routing"], "LOCAL")
        self.assertIn("[LOCAL LLM]", response.data["response"])

    def test_routing_to_cloud(self):
        url = "/api/pro/ai-support/diagnose/"
        data = {
            "server_id": self.cloud_server.id,
            "query": "OutOfMemoryError"
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["routing"], "CLOUD")
        self.assertIn("[CLOUD PREMIUM LLM]", response.data["response"])

    def test_invalid_server(self):
        url = "/api/pro/ai-support/diagnose/"
        data = {
            "server_id": 999,
            "query": "Broken"
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
