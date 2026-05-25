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

            # container.logs(stream=True) returns a blocking generator.
            # We initialize it in a thread to be safe, although the call itself might not block
            # until we start iterating.
            log_stream = await asyncio.to_thread(
                container.logs, stream=True, follow=True, tail=100, stdout=True, stderr=True
            )

            # container.logs can return a generator (on success) or a list (in some mock/edge cases).
            # We ensure we have an iterator.
            try:
                log_iter = iter(log_stream)
            except TypeError:
                logger.error(f"log_stream is not iterable: {type(log_stream)}")
                return

            while True:
                if asyncio.current_task().cancelled():
                    break

                # Each call to next(log_iter) blocks until a new line is available.
                # We offload each blocking call to a thread to keep the event loop responsive.
                def get_next():
                    try:
                        return next(log_iter)
                    except StopIteration:
                        return None

                line = await asyncio.to_thread(get_next)
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
