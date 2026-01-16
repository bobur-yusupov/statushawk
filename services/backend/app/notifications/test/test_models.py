import pytest
from typing import Any
from django.contrib.auth import get_user_model
from faker import Faker
from notifications.models import NotificationChannel, NotificationLog

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


@pytest.mark.django_db
class TestNotificationChannel:
    def test_create_channel(self, user: Any) -> None:
        channel = NotificationChannel.objects.create(
            user=user,
            name="My Telegram",
            provider=NotificationChannel.Provider.TELEGRAM,
            config={"chat_id": "123"},
        )
        assert channel.id is not None  # type: ignore[attr-defined]
        assert channel.user == user
        assert channel.is_active is True

    def test_channel_str(self, channel: Any) -> None:
        assert str(channel) == "Test Channel (telegram)"

    def test_channel_ordering(self, user: Any) -> None:
        c1 = NotificationChannel.objects.create(
            user=user, name="C1", provider="telegram", config={}
        )
        c2 = NotificationChannel.objects.create(
            user=user, name="C2", provider="telegram", config={}
        )
        channels = NotificationChannel.objects.all()
        assert channels[0].id == c2.id  # type: ignore[attr-defined,union-attr]
        assert channels[1].id == c1.id  # type: ignore[attr-defined,union-attr]


@pytest.mark.django_db
class TestNotificationLog:
    def test_create_log(self, channel: Any) -> None:
        log = NotificationLog.objects.create(
            channel=channel,
            monitor_name="Test Monitor",
            status=NotificationLog.Status.SUCCESS,
            payload_sent={"subject": "Test", "message": "Test message"},
        )
        assert log.id is not None  # type: ignore[attr-defined]
        assert log.channel == channel
        assert log.status == NotificationLog.Status.SUCCESS

    def test_log_str(self, channel: Any) -> None:
        log = NotificationLog.objects.create(
            channel=channel,
            monitor_name="Test",
            status=NotificationLog.Status.PENDING,
            payload_sent={},
        )
        assert "pending" in str(log).lower()
