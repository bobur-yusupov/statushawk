from typing import Any
from celery import shared_task
from celery.utils.log import get_task_logger
from .services import NotificationChannelService

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, queue="notification_queue")  # type: ignore[misc]
def send_notification_task(
    self: Any, channel_id: int, subject: str, message: str
) -> str:
    """
    Thin wrapper around the Service Layer.
    """
    service = NotificationChannelService()

    try:
        service.send_alert(channel_id, subject, message)
        return f"Sent to Channel {channel_id}"
    except Exception as exc:
        logger.warning(f"Retry sending to {channel_id} due to: {exc}")
        raise self.retry(exc=exc, countdown=60)
