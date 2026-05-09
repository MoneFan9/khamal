import pytest
from pro.servers.models import Server

@pytest.mark.django_db
def test_server_str():
    server = Server.objects.create(name="Prod Server", hostname_or_ip="1.2.3.4")
    assert str(server) == "Prod Server (1.2.3.4)"
