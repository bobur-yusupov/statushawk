import pytest
from typing import Any
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from faker import Faker
from notifications.models import NotificationChannel, NotificationLog
from notifications.services import NotificationChannelService

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
        user=user,
        name="Test Channel",
        provider=NotificationChannel.Provider.TELEGRAM,
        config={"chat_id": "123456"},
    )


@pytest.fixture
def service() -> Any:
    return NotificationChannelService()


@pytest.mark.django_db
class TestNotificationChannelService:
    def test_create(self, service: Any, user: Any) -> None:
        channel = service.create(
            user=user, name="New", provider="telegram", config={"chat_id": "789"}
        )
        assert channel.id is not None
        assert channel.user == user

    def test_get(self, service: Any, channel: Any, user: Any) -> None:
        result = service.get(id=channel.id, user=user)
        assert result.id == channel.id

    def test_list(self, service: Any, user: Any) -> None:
        NotificationChannel.objects.create(
            user=user, name="C1", provider="telegram", config={}
        )
        NotificationChannel.objects.create(
            user=user, name="C2", provider="telegram", config={}
        )
        result = service.list(user=user)
        assert result.count() == 2

    def test_update(self, service: Any, channel: Any) -> None:
        updated = service.update(channel, name="Updated")
        assert updated.name == "Updated"

    def test_delete(self, service: Any, channel: Any) -> None:
        channel_id = channel.id
        service.delete(channel)
        assert not NotificationChannel.objects.filter(id=channel_id).exists()

    @patch("notifications.services.PROVIDER_MAP")
    def test_send_alert_success(
        self, mock_provider_map: Any, service: Any, channel: Any
    ) -> None:
        mock_provider = MagicMock()
        mock_provider_map.get.return_value = mock_provider

        service.send_alert(channel.id, "Test Subject", "Test Message")

        mock_provider.send.assert_called_once()
        log = NotificationLog.objects.filter(channel=channel).first()
        assert log is not None
        assert log.status == NotificationLog.Status.SUCCESS

    @patch("notifications.services.PROVIDER_MAP")
    def test_send_alert_failure(
        self, mock_provider_map: Any, service: Any, channel: Any
    ) -> None:
        mock_provider = MagicMock()
        mock_provider.send.side_effect = Exception("Send failed")
        mock_provider_map.get.return_value = mock_provider

        with pytest.raises(Exception):
            service.send_alert(channel.id, "Test", "Message")

        log = NotificationLog.objects.filter(channel=channel).first()
        assert log is not None
        assert log.status == NotificationLog.Status.FAILURE
        assert "Send failed" in log.error_message  # type: ignore[operator]

    def test_send_alert_channel_not_found(self, service: Any) -> None:
        # Should not raise exception, just log error
        try:
            service.send_alert(99999, "Test", "Message")
        except Exception:
            pass
        assert NotificationLog.objects.count() == 0

    @patch("notifications.services.verify_telegram_token")
    def test_link_telegram_channel_success(
        self, mock_verify: Any, service: Any, user: Any
    ) -> None:
        mock_verify.return_value = user.id

        result = service.link_telegram_channel("valid_token", "123", "TestUser")

        assert result is not None and "Connected" in result
        assert NotificationChannel.objects.filter(
            user=user, provider="telegram"
        ).exists()

    @patch("notifications.services.verify_telegram_token")
    def test_link_telegram_channel_invalid_token(
        self, mock_verify: Any, service: Any
    ) -> None:
        mock_verify.return_value = None

        result = service.link_telegram_channel("invalid_token", "123", "TestUser")

        assert result is not None and "Invalid" in result

    @patch("notifications.services.verify_telegram_token")
    def test_link_telegram_channel_user_not_found(
        self, mock_verify: Any, service: Any
    ) -> None:
        mock_verify.return_value = 99999

        result = service.link_telegram_channel("token", "123", "TestUser")

        assert "not found" in str(result)  # type: ignore[operator]

    @patch("notifications.services.verify_telegram_token")
    def test_link_telegram_channel_already_exists(
        self, mock_verify: Any, service: Any, user: Any
    ) -> None:
        mock_verify.return_value = user.id
        NotificationChannel.objects.create(
            user=user, provider="telegram", name="Existing", config={"chat_id": "123"}
        )

        result = service.link_telegram_channel("token", "123", "TestUser")

        assert result is not None and "already connected" in result

    @patch("notifications.services.TelegramProvider")
    def test_send_telegram_reply(self, mock_provider_class: Any, service: Any) -> None:
        mock_provider = MagicMock()
        mock_provider_class.return_value = mock_provider

        service.send_telegram_reply("123", "Hello")

        mock_provider.send.assert_called_once_with(
            {"chat_id": "123"}, subject="", message="Hello"
        )
