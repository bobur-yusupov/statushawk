import pytest
from typing import Any
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from faker import Faker
from notifications.models import NotificationChannel
from notifications.tasks import send_notification_task

User = get_user_model()
fake = Faker()


@pytest.fixture
def user() -> Any:
    return User.objects.create_user(
        email=fake.email(), password="testpass123"
    )  # type: ignore[attr-defined]


@pytest.fixture
def channel(user: Any) -> Any:
    return NotificationChannel.objects.create(
        user=user, name="Test", provider="telegram", config={"chat_id": "123"}
    )


@pytest.mark.django_db
class TestNotificationTasks:
    @patch("notifications.tasks.NotificationChannelService")
    def test_send_notification_task_success(
        self, mock_service_class: Any, channel: Any
    ) -> None:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        result = send_notification_task(channel.id, "Test Subject", "Test Message")

        mock_service.send_alert.assert_called_once_with(
            channel.id, "Test Subject", "Test Message"
        )
        assert f"Sent to Channel {channel.id}" in result

    @patch("notifications.tasks.NotificationChannelService")
    def test_send_notification_task_retry(
        self, mock_service_class: Any, channel: Any
    ) -> None:
        mock_service = MagicMock()
        mock_service.send_alert.side_effect = Exception("Network error")
        mock_service_class.return_value = mock_service

        with pytest.raises(Exception):
            send_notification_task(channel.id, "Subject", "Message")
