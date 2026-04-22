from django.db import models
from django.core.validators import MinValueValidator

class Server(models.Model):
    """
    Represents a physical or virtual machine managed by Khamal Enterprise.
    """
    class Status(models.TextChoices):
        ONLINE = "ONLINE", "Online"
        OFFLINE = "OFFLINE", "Offline"
        MAINTENANCE = "MAINTENANCE", "Maintenance"
        ERROR = "ERROR", "Error"

    name = models.CharField(max_length=255)
    hostname_or_ip = models.CharField(max_length=255, unique=True)
    ssh_port = models.PositiveIntegerField(default=22)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OFFLINE,
        db_index=True
    )
    is_active = models.BooleanField(default=True)

    # System Info (updated via agent heartbeats/discovery)
    os_info = models.CharField(max_length=255, blank=True, null=True)
    cpu_cores = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)]
    )
    memory_total = models.BigIntegerField(
        blank=True,
        null=True,
        help_text="Total memory in bytes",
        validators=[MinValueValidator(0)]
    )

    last_heartbeat = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.hostname_or_ip})"

    class Meta:
        verbose_name = "Server"
        verbose_name_plural = "Servers"
        ordering = ["-created_at"]
