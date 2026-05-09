from django.test import TestCase
from pro.servers.models import Server

class ServerExtendedTests(TestCase):
    def test_str_method(self):
        server = Server(name="Backup Server", hostname_or_ip="10.0.0.5")
        assert str(server) == "Backup Server (10.0.0.5)"
