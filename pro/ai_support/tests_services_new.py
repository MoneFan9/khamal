import pytest
from unittest.mock import MagicMock, patch
from pro.ai_support.services import RouterService, LLMService
from pro.ai_support.models import DiagnosticRequest
from pro.servers.models import Server
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="password")

@pytest.fixture
def server(db):
    return Server.objects.create(
        name="TestServer",
        hostname_or_ip="127.0.0.1",
        cpu_cores=4,
        memory_total=8 * 1024 * 1024 * 1024
    )

@pytest.mark.django_db
class TestRouterService:
    def test_route_request_local(self, server):
        # 4 cores, 8GB RAM -> LOCAL
        assert RouterService.route_request(server) == DiagnosticRequest.Routing.LOCAL

    def test_route_request_cloud_low_cpu(self, server):
        server.cpu_cores = 2
        assert RouterService.route_request(server) == DiagnosticRequest.Routing.CLOUD

    def test_route_request_cloud_low_ram(self, server):
        server.memory_total = 4 * 1024 * 1024 * 1024
        assert RouterService.route_request(server) == DiagnosticRequest.Routing.CLOUD

    @patch("pro.ai_support.services.LLMService.get_local_diagnostic")
    def test_process_diagnostic_local(self, mock_local, user, server):
        mock_local.return_value = "Local response"
        diag = RouterService.process_diagnostic(user, server, "Test query")

        assert diag.routing == DiagnosticRequest.Routing.LOCAL
        assert diag.response == "Local response"
        assert DiagnosticRequest.objects.count() == 1
        mock_local.assert_called_once_with(server, "Test query")

    @patch("pro.ai_support.services.LLMService.get_cloud_diagnostic")
    def test_process_diagnostic_cloud(self, mock_cloud, user, server):
        server.cpu_cores = 2
        mock_cloud.return_value = "Cloud response"
        diag = RouterService.process_diagnostic(user, server, "Test query")

        assert diag.routing == DiagnosticRequest.Routing.CLOUD
        assert diag.response == "Cloud response"
        mock_cloud.assert_called_once_with(server, "Test query")

class TestLLMService:
    @patch("pro.ai_support.services.OllamaClient")
    def test_get_local_diagnostic(self, mock_client_cls, server):
        mock_client = mock_client_cls.return_value
        # Mock the session context manager
        mock_client.session.return_value.__enter__.return_value = None

        response = LLMService.get_local_diagnostic(server, "query")
        assert "[LOCAL LLM]" in response
        assert server.name in response

    def test_get_cloud_diagnostic(self, server):
        response = LLMService.get_cloud_diagnostic(server, "query")
        assert "[CLOUD PREMIUM LLM]" in response
        assert server.name in response
