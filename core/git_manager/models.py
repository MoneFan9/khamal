from django.db import models
from projects.models import Project

class Repository(models.Model):
    """
    Represents a Git repository associated with a project.
    """
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="repository"
    )
    url = models.URLField(max_length=500)
    local_path = models.CharField(max_length=1024)
    current_branch = models.CharField(max_length=255, default="main")
    last_pull_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Repo for {self.project.name} ({self.url})"

    class Meta:
        verbose_name_plural = "Repositories"
