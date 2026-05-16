from rest_framework import viewsets, permissions
from .models import Server
from .serializers import ServerSerializer

class ServerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows servers to be viewed or edited.
    """
    queryset = Server.objects.only(
        'id', 'name', 'hostname_or_ip', 'ssh_port', 'status',
        'is_active', 'os_info', 'cpu_cores', 'memory_total',
        'last_heartbeat', 'created_at', 'updated_at'
    )
    serializer_class = ServerSerializer
    permission_classes = [permissions.IsAuthenticated]
