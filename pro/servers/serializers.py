from rest_framework import serializers
from .models import Server

class ServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Server
        fields = [
            'id', 'name', 'hostname_or_ip', 'ssh_port', 'status',
            'is_active', 'os_info', 'cpu_cores', 'memory_total',
            'last_heartbeat', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'os_info', 'cpu_cores',
            'memory_total', 'last_heartbeat', 'created_at', 'updated_at'
        ]

