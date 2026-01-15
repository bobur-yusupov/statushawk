import requests
import logging
from django.conf import settings
from django.core.mail import send_mail
from common.services import BaseService
from .models import NotificationChannel, NotificationLog
from .crud import NotificationChannelCRUD, NotificationLogCRUD

logger = logging.getLogger(__name__)

class NotificationChannelService(BaseService[NotificationChannel]):
    """
    Handles CRUD for channel settings + The Logic to actually send alerts.
    """
    model = NotificationChannel
    crud_class = NotificationChannelCRUD

    def send_alert(self, channel_id: int, subject: str, message: str):
        channel = self.crud.get(id=channel_id) 
        if not channel:
            logger.error(f"Channel {channel_id} not found.")
            return

        log_crud = NotificationLogCRUD()
        log = log_crud.create(
            channel=channel,
            monitor_name=subject,
            payload_sent={"subject": subject, "message": message},
            status=NotificationLog.Status.PENDING
        )

        try:
            if channel.provider == NotificationChannel.Provider.SLACK:
                self._send_slack(channel.config, subject, message)
            
            elif channel.provider == NotificationChannel.Provider.TELEGRAM:
                self._send_telegram(channel.config, message)
            
            elif channel.provider == NotificationChannel.Provider.EMAIL:
                self._send_email(channel.config, subject, message)
            
            elif channel.provider == NotificationChannel.Provider.WEBHOOK:
                self._send_webhook(channel.config, subject, message)

            # 4. Success Update
            log_crud.update(log, status=NotificationLog.Status.SUCCESS)
            logger.info(f"✅ Alert sent to {channel}")

        except Exception as e:
            # 5. Failure Update
            log_crud.update(log, status=NotificationLog.Status.FAILURE, error_message=str(e))
            logger.error(f"❌ Failed to send to {channel}: {e}")
            raise e

    def _send_slack(self, config: dict, subject: str, message: str):
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            raise ValueError("Missing 'webhook_url'")

        payload = {
            "text": f"*{subject}*\n{message}",
            "blocks": [
                {"type": "section", "text": {"type": "mrkdwn", "text": f"*{subject}*"}},
                {"type": "section", "text": {"type": "mrkdwn", "text": message}}
            ]
        }
        requests.post(webhook_url, json=payload, timeout=10).raise_for_status()

    def _send_telegram(self, config: dict, message: str):
        chat_id = config.get("chat_id")
        token = settings.TELEGRAM_BOT_TOKEN
        if not chat_id or not token:
            raise ValueError("Missing 'chat_id' or 'TELEGRAM_BOT_TOKEN'")

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=10).raise_for_status()

    def _send_email(self, config: dict, subject: str, message: str):
        email = config.get("email")
        if not email:
            raise ValueError("Missing 'email'")

        send_mail(
            subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False
        )

    def _send_webhook(self, config: dict, subject: str, message: str):
        url = config.get("url")
        if not url:
            raise ValueError("Missing 'url'")
            
        requests.post(url, json={"subject": subject, "message": message}, timeout=10).raise_for_status()