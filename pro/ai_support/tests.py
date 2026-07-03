from django.test import TestCase
from django.contrib.auth import get_user_model
from pro.servers.models import Server
from pro.ai_support.models import DiagnosticRequest
from pro.ai_support.services import RouterService, LLMService
from unittest.mock import patch, MagicMock

User = get_user_model()

class AISupportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        self.server_powerful = Server.objects.create(
            name="Powerful Server",
            hostname_or_ip="10.0.0.1",
            cpu_cores=8,
            memory_total=16 * 1024 * 1024 * 1024
        )
        self.server_weak = Server.objects.create(
            name="Weak Server",
            hostname_or_ip="10.0.0.2",
            cpu_cores=2,
            memory_total=4 * 1024 * 1024 * 1024
        )

    def test_route_request_local(self):
        routing = RouterService.route_request(self.server_powerful)
        self.assertEqual(routing, DiagnosticRequest.Routing.LOCAL)

    def test_route_request_cloud(self):
        routing = RouterService.route_request(self.server_weak)
        self.assertEqual(routing, DiagnosticRequest.Routing.CLOUD)

    @patch("pro.ai_support.services.LLMService.get_local_diagnostic")
    def test_process_diagnostic_local(self, mock_local):
        mock_local.return_value = "Mocked local response"
        diag = RouterService.process_diagnostic(
            user=self.user,
            server=self.server_powerful,
            query="Check health"
        )
        self.assertEqual(diag.routing, DiagnosticRequest.Routing.LOCAL)
        self.assertEqual(diag.response, "Mocked local response")
        self.assertEqual(DiagnosticRequest.objects.count(), 1)

    @patch("pro.ai_support.services.LLMService.get_cloud_diagnostic")
    def test_process_diagnostic_cloud(self, mock_cloud):
        mock_cloud.return_value = "Mocked cloud response"
        diag = RouterService.process_diagnostic(
            user=self.user,
            server=self.server_weak,
            query="Check health"
        )
        self.assertEqual(diag.routing, DiagnosticRequest.Routing.CLOUD)
        self.assertEqual(diag.response, "Mocked cloud response")

    @patch("core.ai.client.OllamaClient.session")
    def test_llm_service_local(self, mock_session):
        mock_session.return_value.__enter__.return_value = MagicMock()
        response = LLMService.get_local_diagnostic(self.server_powerful, "Query")
        self.assertIn("[LOCAL LLM]", response)

    def test_llm_service_cloud(self):
        response = LLMService.get_cloud_diagnostic(self.server_weak, "Query")
        self.assertIn("[CLOUD PREMIUM LLM]", response)

from rest_framework.test import APITestCase
from django.urls import reverse

class AISupportAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="apiuser", password="password")
        self.client.force_authenticate(user=self.user)
        self.server = Server.objects.create(
            name="API Server",
            hostname_or_ip="10.0.0.3",
            cpu_cores=4,
            memory_total=8 * 1024 * 1024 * 1024
        )
        self.url = reverse("ai-diagnose")

    def test_diagnostic_api_success(self):
        data = {"server_id": self.server.id, "query": "Status?"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 201)
        self.assertIn("response", response.data)

    def test_diagnostic_api_invalid_data(self):
        data = {"server_id": 999, "query": ""}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)

    def test_diagnostic_api_unauthenticated(self):
        self.client.force_authenticate(user=None)
        data = {"server_id": self.server.id, "query": "Status?"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 403)
