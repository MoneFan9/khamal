from rest_framework import serializers
from .models import DiagnosticRequest

class DiagnosticRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticRequest
        fields = [
            "id", "server", "query", "routing",
            "response", "is_successful", "created_at"
        ]
        read_only_fields = ["routing", "response", "is_successful", "created_at"]

class DiagnosticInputSerializer(serializers.Serializer):
    server_id = serializers.IntegerField()
    query = serializers.CharField()
