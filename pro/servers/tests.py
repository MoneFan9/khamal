from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Server

User = get_user_model()

class ServerAPITestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client = APIClient()
        self.server_data = {
            "name": "Production Node 1",
            "hostname_or_ip": "192.168.1.100",
            "ssh_port": 22
        }

    def test_create_server_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/servers/", self.server_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Server.objects.count(), 1)

    def test_create_server_unauthenticated(self):
        response = self.client.post("/api/servers/", self.server_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_read_only_fields_protection(self):
        self.client.force_authenticate(user=self.user)
        # Create server with initial status OFFLINE
        server = Server.objects.create(**self.server_data)
        self.assertEqual(server.status, Server.Status.OFFLINE)

        # Try to update status via API (should be ignored as it is read-only)
        update_data = {"status": Server.Status.ONLINE}
        response = self.client.patch(f"/api/servers/{server.id}/", update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        server.refresh_from_db()
        self.assertEqual(server.status, Server.Status.OFFLINE)

    def test_invalid_ssh_port(self):
        self.client.force_authenticate(user=self.user)
        invalid_data = self.server_data.copy()
        invalid_data["ssh_port"] = 70000
        response = self.client.post("/api/servers/", invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
