import json
import asyncio
import docker
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Deployment
from .docker_client import get_docker_client

class LogConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.deployment_id = self.scope['url_route']['kwargs']['deployment_id']
        self.deployment = await self.get_deployment(self.deployment_id)

        if self.deployment is None:
            await self.close()
            return

        # Check permission (assuming request.user is available in scope)
        user = self.scope.get('user')
        if not user or not await self.check_permission(user, self.deployment):
            await self.close()
            return

        await self.accept()

        self.streaming_task = asyncio.create_task(self.stream_logs())

    async def disconnect(self, _close_code):
        if hasattr(self, 'streaming_task'):
            self.streaming_task.cancel()

    async def stream_logs(self):
        client = get_docker_client()
        try:
            container_id = await self.get_container_id()
            if not container_id:
                await self.send(text_data=json.dumps({'log': 'Container not found.'}))
                return

            container = client.containers.get(container_id)

            def get_log_stream():
                return container.logs(stream=True, follow=True, tail=100, stdout=True, stderr=True)

            log_stream = await asyncio.to_thread(get_log_stream)

            # Define a synchronous wrapper to get the next line from the blocking generator
            def get_next_line(stream_iter):
                try:
                    return next(stream_iter)
                except StopIteration:
                    return None

            stream_iter = iter(log_stream)
            while True:
                if asyncio.current_task().cancelled():
                    break

                # fetch the next line in a separate thread to avoid blocking the event loop
                line = await asyncio.to_thread(get_next_line, stream_iter)
                if line is None:
                    break

                await self.send(text_data=json.dumps({
                    'log': line.decode('utf-8', errors='replace')
                }))

        except Exception as e:
            await self.send(text_data=json.dumps({'error': str(e)}))
        finally:
            client.close()

    @database_sync_to_async
    def get_deployment(self, deployment_id):
        try:
            return Deployment.objects.get(id=deployment_id)
        except Deployment.DoesNotExist:
            return None

    @database_sync_to_async
    def get_container_id(self):
        self.deployment.refresh_from_db()
        return self.deployment.container_id

    @database_sync_to_async
    def check_permission(self, user, deployment):
        # Basic check: user must be the owner of the project
        return deployment.project.owner == user
