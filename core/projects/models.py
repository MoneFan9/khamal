from django.db import models
from django.conf import settings
from django.utils.text import slugify

class Project(models.Model):
    """
    Represents a project in Khamal.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    network_id = models.CharField(max_length=255, blank=True, null=True)
    domain = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.domain:
            suffix = getattr(settings, 'KHAMAL_DEFAULT_DOMAIN_SUFFIX', 'khamal.local')
            self.domain = f"{slugify(self.name)}.{suffix}"
        super().save(*args, **kwargs)

class Deployment(models.Model):
    """
    Represents a deployment instance of a project.
    """
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        STARTING = "STARTING", "Starting"
        RUNNING = "RUNNING", "Running"
        STOPPING = "STOPPING", "Stopping"
        STOPPED = "STOPPED", "Stopped"
        RESTARTING = "RESTARTING", "Restarting"
        FAILED = "FAILED", "Failed"
        REMOVED = "REMOVED", "Removed"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="deployments"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    container_id = models.CharField(max_length=255, blank=True, null=True)
    container_port = models.PositiveIntegerField(default=80)
    hot_reload = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} - {self.status} ({self.created_at})"

class DatabaseInstance(models.Model):
    """
    Persists database credentials and configuration for a project.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="database_instances"
    )
    engine = models.CharField(max_length=50) # e.g., postgres, redis
    container_name = models.CharField(max_length=255)
    db_name = models.CharField(max_length=255, default="khamal")
    db_user = models.CharField(max_length=255, default="khamal")
    db_password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.engine} for {self.project.name}"

class Backup(models.Model):
    """
    Tracks database backups.
    """
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    db_instance = models.ForeignKey(
        DatabaseInstance,
        on_delete=models.CASCADE,
        related_name="backups"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    file_path = models.CharField(max_length=1024, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Backup {self.id} - {self.db_instance.engine} - {self.status}"
