from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/logs/(?P<deployment_id>\d+)/$', consumers.LogConsumer.as_asgi()),
]
