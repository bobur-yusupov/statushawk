from typing import Any
from django.db import models, transaction
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
    url = models.URLField(validators=[URLValidator()], max_length=2048)
    monitor_type = models.CharField(max_length=10, choices=MonitorType.choices)
    status = models.CharField(
        max_length=10, choices=StatusType.choices, default=StatusType.PAUSED
    )

    interval = models.PositiveIntegerField(
        default=300, validators=[MinValueValidator(30)]
    )
    is_active = models.BooleanField(default=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
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
        is_new = self.pk is None
        was_active = False
        if not is_new:
            try:
                old_instance = Monitor.objects.get(pk=self.pk)
                was_active = old_instance.is_active
            except Monitor.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)

        if self.is_active and (is_new or not was_active):
            from monitor.tasks import check_monitor_task
            
            transaction.on_commit(
                lambda: check_monitor_task.apply_async(
                    kwargs={'monitor_id': self.pk},
                    queue='runner_queue',
                )
            )
        

class MonitorResult(models.Model):
    id = models.AutoField(primary_key=True, unique=True, editable=False)
    monitor = models.ForeignKey(
        Monitor, on_delete=models.CASCADE, related_name="results"
    )
    status_code = models.PositiveIntegerField(null=True, blank=True)
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    is_up = models.BooleanField()
    checked_at = models.DateTimeField(auto_now_add=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        verbose_name = _("Monitor Result")
        verbose_name_plural = _("Monitor Results")
        ordering = ("-checked_at",)
        indexes = [
            models.Index(fields=["monitor", "checked_at"]),
        ]

    def __str__(self) -> str:
        return f"Result for {self.monitor.name} at {self.checked_at}"
