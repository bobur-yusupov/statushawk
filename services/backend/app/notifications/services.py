from typing import Optional
import logging
from django.contrib.auth import get_user_model
from common.services import BaseService
from .models import NotificationChannel, NotificationLog
from .crud import NotificationChannelCRUD, NotificationLogCRUD
from .providers import PROVIDER_MAP, TelegramProvider
from .utils import verify_telegram_token

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationChannelService(BaseService[NotificationChannel]):
    """
    Handles CRUD for channel settings + The Logic to actually send alerts.
    """

    model = NotificationChannel
    crud_class = NotificationChannelCRUD

    def _create_log(
        self, channel: NotificationChannel, subject: str, message: str
    ) -> NotificationLog:
        """Create a notification log entry."""
        return NotificationLogCRUD().create(
            channel=channel,
            monitor_name=subject,
            payload_sent={"subject": subject, "message": message},
            status=NotificationLog.Status.PENDING,
        )

    def _update_log(
        self, log: NotificationLog, status: str, error_msg: Optional[str] = None
    ) -> None:
        NotificationLogCRUD().update(log, status=status, error_message=error_msg)

    def send_alert(self, channel_id: int, subject: str, message: str) -> None:
        channel = self.crud.get(id=channel_id)
        if not channel:
            logger.error(f"Channel {channel_id} not found.")
            return

        log = self._create_log(channel=channel, subject=subject, message=message)

        try:
            provider = PROVIDER_MAP.get(channel.provider)
            if not provider:
                raise ValueError(f"Provider {channel.provider} is not supported.")
            provider.send(channel.config, subject, message)

            self._update_log(log, status=NotificationLog.Status.SUCCESS)
            logger.info(f"Alert sent to {channel}")

        except Exception as e:
            # 5. Failure Update
            self._update_log(
                log, status=NotificationLog.Status.FAILURE, error_msg=str(e)
            )
            logger.error(f"Failed to send to {channel}: {e}")
            raise e

    def link_telegram_channel(self, token: str, chat_id: str, user_name: str) -> str:
        """
        Links a Telegram chat to a user and returns the message to send back.
        """
        user_id = verify_telegram_token(token=token)
        if not user_id:
            return "Invalid or expired token."

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return "System error: User not found."

        exists = NotificationChannel.objects.filter(
            provider=NotificationChannel.Provider.TELEGRAM, config__chat_id=chat_id
        ).exists()

        if exists:
            return "You are already connected."

        NotificationChannel.objects.create(
            user=user,
            provider=NotificationChannel.Provider.TELEGRAM,
            name=f"Telegram ({user_name})",
            config={"chat_id": chat_id},
        )
        return f"Connected! Hello {user.first_name}"

    def send_telegram_reply(self, chat_id: str, message: str) -> None:
        """Wrapper to send a simple reply."""
        try:
            TelegramProvider().send({"chat_id": chat_id}, subject="", message=message)
        except Exception as e:
            logger.error(f"Failed to reply to Telegram {chat_id}: {e}")
