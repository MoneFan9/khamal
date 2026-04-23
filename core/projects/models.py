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
