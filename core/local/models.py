from django.db import models
from projects.models import Project

class LocalSource(models.Model):
    """
    Represents a local directory on the host to be mounted in the container.
    Used for Hot-Reload development.
    """
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="local_source"
    )
    host_path = models.CharField(
        max_length=1024,
        help_text="Absolute path on the host machine."
    )
    container_path = models.CharField(
        max_length=1024,
        default="/app",
        help_text="Path inside the container where the host_path will be mounted."
    )

    def __str__(self):
        return f"Local source for {self.project.name} ({self.host_path})"
