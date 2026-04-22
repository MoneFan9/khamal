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

    def validate_ssh_port(self, value):
        if value < 1 or value > 65535:
            raise serializers.ValidationError("Port must be between 1 and 65535.")
        return value
