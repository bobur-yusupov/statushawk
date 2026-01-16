from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class NotificationChannel(models.Model):
    class Provider(models.TextChoices):
        EMAIL = "email", _("Email")
        SLACK = "slack", _("Slack")
        TELEGRAM = "telegram", _("Telegram")
        CONSOLE = "console", _("Console (Debug)")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_channels",
    )
    name = models.CharField(max_length=100, help_text="My DevOps Slack")
    provider = models.CharField(max_length=20, choices=Provider.choices)

    config = models.JSONField(default=dict)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.provider})"


class NotificationLog(models.Model):
    """
    Audit trail: 'Did I get that alert?'
    """

    class Status(models.TextChoices):
        SUCCESS = "success", _("Success")
        FAILURE = "failure", _("Failure")
        PENDING = "pending", _("Pending")

    channel = models.ForeignKey(
        NotificationChannel, on_delete=models.CASCADE, related_name="logs"
    )

    monitor_name = models.CharField(max_length=255)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    error_message = models.TextField(blank=True, null=True)

    payload_sent = models.JSONField(help_text="Copy of what we sent")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.channel} - {self.status} at {self.created_at}"
