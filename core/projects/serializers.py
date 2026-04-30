import os
from django.conf import settings
from rest_framework import serializers
from .models import Project, Deployment
from local.models import LocalSource

class LocalSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalSource
        fields = ['host_path', 'container_path']

    def validate_host_path(self, value):
        """
        Validates that the host_path is absolute, normalized, and within an allowed directory.
        """
        # Ensure it's an absolute path
        if not os.path.isabs(value):
            raise serializers.ValidationError("host_path must be an absolute path.")

        # Normalize the path to remove .. and other traversal sequences
        # We use realpath to resolve any symlinks and prevent bypasses
        try:
            target_path = os.path.realpath(value)
            allowed_base = os.path.realpath(str(settings.BASE_DIR))
        except Exception as e:
            raise serializers.ValidationError(f"Path resolution error: {e}")

        if os.path.commonpath([allowed_base, target_path]) != allowed_base:
            raise serializers.ValidationError(f"Access to {value} is denied. Paths must be within {allowed_base}")

        return target_path

class ProjectSerializer(serializers.ModelSerializer):
    owner_username = serializers.ReadOnlyField(source='owner.username')
    local_source = LocalSourceSerializer(required=False, allow_null=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'domain', 'owner', 'owner_username', 'local_source', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'owner_username', 'created_at', 'updated_at']

    def create(self, validated_data):
        local_source_data = validated_data.pop('local_source', None)
        project = Project.objects.create(**validated_data)
        if local_source_data:
            LocalSource.objects.create(project=project, **local_source_data)
        return project

    def update(self, instance, validated_data):
        local_source_data = validated_data.pop('local_source', None)

        # Update project fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update or create local source
        if local_source_data:
            LocalSource.objects.update_or_create(
                project=instance,
                defaults=local_source_data
            )
        elif hasattr(instance, 'local_source'):
            instance.local_source.delete()

        return instance

class DeploymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deployment
        fields = ['id', 'project', 'status', 'container_id', 'container_port', 'hot_reload', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'container_id', 'created_at', 'updated_at']
