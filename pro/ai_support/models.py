from django.db import models
from django.conf import settings
from pro.servers.models import Server

class DiagnosticRequest(models.Model):
    class Routing(models.TextChoices):
        LOCAL = "LOCAL", "Local LLM"
        CLOUD = "CLOUD", "Cloud Premium LLM"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="diagnostic_requests"
    )
    server = models.ForeignKey(
        Server,
        on_delete=models.CASCADE,
        related_name="diagnostics"
    )
    query = models.TextField()
    routing = models.CharField(
        max_length=10,
        choices=Routing.choices,
        db_index=True
    )
    response = models.TextField(blank=True, null=True)
    is_successful = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Diag for {self.server.name} by {self.user.username} ({self.routing})"

    class Meta:
        ordering = ["-created_at"]
