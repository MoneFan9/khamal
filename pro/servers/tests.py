from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from pro.servers.models import Server
from django.urls import reverse

User = get_user_model()

class ServerAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="serveruser", password="password")
        self.client.force_authenticate(user=self.user)
        self.server = Server.objects.create(
            name="Test Server",
            hostname_or_ip="10.0.0.4",
            cpu_cores=2,
            memory_total=4096
        )
        # Check reverse name, might be server-list or similar depending on router
        self.list_url = reverse("server-list")
        self.detail_url = reverse("server-detail", kwargs={"pk": self.server.id})

    def test_list_servers(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_get_server_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Test Server")

    def test_create_server(self):
        data = {"name": "New Server", "hostname_or_ip": "1.2.3.4", "ssh_port": 22}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Server.objects.count(), 2)

    def test_update_server(self):
        data = {"name": "Updated Server"}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, 200)
        self.server.refresh_from_db()
        self.assertEqual(self.server.name, "Updated Server")

    def test_delete_server(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Server.objects.count(), 0)

    def test_unauthenticated_access(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 403)

    def test_invalid_ssh_port(self):
        data = {"ssh_port": 70000}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("ssh_port", response.data)
