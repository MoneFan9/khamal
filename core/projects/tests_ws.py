import pytest
import json
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from core.khamal.asgi import application
from projects.models import Project, Deployment
from unittest.mock import patch, MagicMock

User = get_user_model()

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_log_consumer_unauthenticated():
    communicator = WebsocketCommunicator(application, "/ws/logs/1/")
    connected, subprotocol = await communicator.connect()
    assert not connected
    await communicator.disconnect()

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_log_consumer_not_found():
    user = await User.objects.acreate(username="testuser", password="password")
    communicator = WebsocketCommunicator(application, "/ws/logs/999/")
    communicator.scope['user'] = user
    connected, subprotocol = await communicator.connect()
    assert not connected
    await communicator.disconnect()

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_log_consumer_no_permission():
    owner = await User.objects.acreate(username="owner", password="password")
    other_user = await User.objects.acreate(username="other", password="password")
    project = await Project.objects.acreate(name="Test Project", owner=owner)
    deployment = await Deployment.objects.acreate(project=project)

    communicator = WebsocketCommunicator(application, f"/ws/logs/{deployment.id}/")
    communicator.scope['user'] = other_user
    connected, subprotocol = await communicator.connect()
    assert not connected
    await communicator.disconnect()

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_log_consumer_success():
    user = await User.objects.acreate(username="user", password="password")
    project = await Project.objects.acreate(name="Test Project", owner=user)
    deployment = await Deployment.objects.acreate(project=project, container_id="test_container")

    with patch('projects.consumers.get_docker_client') as mock_get_client:
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_container.logs.return_value = [b"log line 1\n", b"log line 2\n"]
        mock_client.containers.get.return_value = mock_container
        mock_get_client.return_value = mock_client

        communicator = WebsocketCommunicator(application, f"/ws/logs/{deployment.id}/")
        communicator.scope['user'] = user
        connected, subprotocol = await communicator.connect()
        assert connected

        response1 = await communicator.receive_from()
        assert json.loads(response1) == {"log": "log line 1\n"}

        response2 = await communicator.receive_from()
        assert json.loads(response2) == {"log": "log line 2\n"}

        await communicator.disconnect()
