import pytest
import json
from unittest.mock import patch, MagicMock
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from khamal.asgi import application
from projects.models import Project, Deployment
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_log_consumer_no_deployment():
    communicator = WebsocketCommunicator(application, "/ws/logs/999/")
    connected, _ = await communicator.connect()
    assert not connected

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_log_consumer_no_permission():
    user = await database_sync_to_async(User.objects.create_user)(username="user1", password="password")
    other_user = await database_sync_to_async(User.objects.create_user)(username="user2", password="password")
    project = await database_sync_to_async(Project.objects.create)(name="P1", owner=other_user)
    deployment = await database_sync_to_async(Deployment.objects.create)(project=project)

    communicator = WebsocketCommunicator(application, f"/ws/logs/{deployment.id}/")
    communicator.scope['user'] = user
    connected, _ = await communicator.connect()
    assert not connected

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_log_consumer_success():
    user = await database_sync_to_async(User.objects.create_user)(username="user3", password="password")
    project = await database_sync_to_async(Project.objects.create)(name="P2", owner=user)
    deployment = await database_sync_to_async(Deployment.objects.create)(project=project, container_id="c123")

    with patch("projects.consumers.get_docker_client") as mock_docker:
        mock_client = MagicMock()
        mock_docker.return_value = mock_client
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container
        mock_container.logs.return_value = [b"line1\n", b"line2\n"]

        communicator = WebsocketCommunicator(application, f"/ws/logs/{deployment.id}/")
        communicator.scope['user'] = user
        connected, _ = await communicator.connect()
        assert connected

        response = await communicator.receive_json_from()
        assert response == {"log": "line1\n"}
        response = await communicator.receive_json_from()
        assert response == {"log": "line2\n"}

        await communicator.disconnect()
