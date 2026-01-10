from typing import Any
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, URLValidator
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Monitor(models.Model):
    class MonitorType(models.TextChoices):
        HTTP = "HTTP", _("HTTP(s)")
        PING = "PING", _("PING")
        TCP = "TCP", _("TCP")
    

    class StatusType(models.TextChoices):
        UP = "UP", _("UP")
        DOWN = "DOWN", _("DOWN")
        PAUSED = "PAUSED", _("PAUSED")


    id = models.AutoField(primary_key=True, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="monitors")
    name = models.CharField(max_length=255)
    url = models.URLField(validators=[URLValidator()])
    monitor_type = models.CharField(max_length=10, choices=MonitorType.choices)
    status = models.CharField(max_length=10, choices=StatusType.choices, default=StatusType.PAUSED)

    interval = models.PositiveIntegerField(
        default=60, validators=[MinValueValidator(30)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Monitor")
        verbose_name_plural = _("Monitors")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.url})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        super().save(*args, **kwargs)
        self._trigger_sync()

    def _trigger_sync(self) -> None:
        pass
