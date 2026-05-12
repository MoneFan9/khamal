import pytest
from django.contrib.auth import get_user_model
from pro.servers.models import Server
from pro.ai_support.models import DiagnosticRequest
from pro.ai_support.serializers import DiagnosticRequestSerializer, DiagnosticInputSerializer
from rest_framework import serializers

User = get_user_model()

@pytest.mark.django_db
def test_diagnostic_input_serializer_validation():
    server = Server.objects.create(name="Test Server", hostname_or_ip="1.2.3.4", cpu_cores=4, memory_total=8*1024*1024*1024)

    data = {
        "server_id": server.id,
        "query": "Help me"
    }
    serializer = DiagnosticInputSerializer(data=data)
    assert serializer.is_valid()

    # Missing server_id
    data = {"query": "Help"}
    serializer = DiagnosticInputSerializer(data=data)
    assert not serializer.is_valid()
    assert "server_id" in serializer.errors

@pytest.mark.django_db
def test_server_status_transitions():
    server = Server.objects.create(
        name="Transition Server",
        hostname_or_ip="5.6.7.8",
        cpu_cores=1,
        memory_total=1024
    )
    assert server.status == Server.Status.OFFLINE

    server.status = Server.Status.ONLINE
    server.save()
    assert Server.objects.get(id=server.id).status == Server.Status.ONLINE

@pytest.mark.django_db
def test_diagnostic_request_creation():
    user = User.objects.create_user(username="user2", password="password")
    server = Server.objects.create(name="S1", hostname_or_ip="1.1.1.1", cpu_cores=1, memory_total=1024)
    diag = DiagnosticRequest.objects.create(
        user=user,
        server=server,
        query="Why?",
        routing=DiagnosticRequest.Routing.LOCAL,
        response="Because."
    )
    assert diag.user == user
    assert diag.server == server
    assert diag.routing == "LOCAL"
    assert diag.response == "Because."

@pytest.mark.django_db
def test_diagnostic_request_serializer_output():
    user = User.objects.create_user(username="user3", password="password")
    server = Server.objects.create(name="S2", hostname_or_ip="2.2.2.2", cpu_cores=1, memory_total=1024)
    diag = DiagnosticRequest.objects.create(
        user=user,
        server=server,
        query="What?",
        routing=DiagnosticRequest.Routing.CLOUD,
        response="Everything."
    )
    serializer = DiagnosticRequestSerializer(diag)
    assert serializer.data["query"] == "What?"
    assert serializer.data["routing"] == "CLOUD"
    assert serializer.data["response"] == "Everything."
