from django.test import TestCase
from pro.servers.models import Server

class ServerExtendedTests(TestCase):
    def test_server_str(self):
        server = Server.objects.create(name="Main Server", hostname_or_ip="1.2.3.4")
        self.assertEqual(str(server), "Main Server (1.2.3.4)")
