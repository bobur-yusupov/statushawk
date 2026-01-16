import pytest
from typing import Any
from django.contrib.auth import get_user_model
from faker import Faker
from notifications.models import NotificationChannel, NotificationLog
from notifications.crud import NotificationChannelCRUD, NotificationLogCRUD

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
class TestNotificationChannelCRUD:
    def test_create(self, user: Any) -> None:
        crud = NotificationChannelCRUD()
        channel = crud.create(
            user=user, name="New", provider="telegram", config={"chat_id": "456"}
        )
        assert channel.id is not None  # type: ignore[attr-defined]
        assert channel.user == user

    def test_get(self, user: Any, channel: Any) -> None:
        crud = NotificationChannelCRUD()
        result = crud.get(
            id=channel.id, user=user
        )  # type: ignore[attr-defined,union-attr]
        assert result.id == channel.id  # type: ignore[attr-defined,union-attr]

    def test_list(self, user: Any) -> None:
        crud = NotificationChannelCRUD()
        NotificationChannel.objects.create(
            user=user, name="C1", provider="telegram", config={}
        )
        NotificationChannel.objects.create(
            user=user, name="C2", provider="telegram", config={}
        )
        result = crud.list(user=user)
        assert result.count() == 2

    def test_update(self, channel: Any) -> None:
        crud = NotificationChannelCRUD()
        updated = crud.update(channel, name="Updated")
        assert updated.name == "Updated"

    def test_delete(self, channel: Any) -> None:
        crud = NotificationChannelCRUD()
        channel_id = channel.id
        crud.delete(channel)
        assert not NotificationChannel.objects.filter(
            id=channel_id
        ).exists()  # type: ignore[attr-defined]

    def test_filter(self, user: Any) -> None:
        crud = NotificationChannelCRUD()
        NotificationChannel.objects.create(
            user=user, name="Active", provider="telegram", config={}, is_active=True
        )
        NotificationChannel.objects.create(
            user=user, name="Inactive", provider="telegram", config={}, is_active=False
        )
        result = crud.filter(user=user, is_active=True)
        assert result.count() == 1


@pytest.mark.django_db
class TestNotificationLogCRUD:
    def test_create(self, channel: Any) -> None:
        crud = NotificationLogCRUD()
        log = crud.create(
            channel=channel,
            monitor_name="Test",
            status=NotificationLog.Status.PENDING,
            payload_sent={},
        )
        assert log.id is not None  # type: ignore[attr-defined]
        assert log.channel == channel

    def test_list(self, channel: Any) -> None:
        crud = NotificationLogCRUD()
        NotificationLog.objects.create(
            channel=channel, monitor_name="M1", status="success", payload_sent={}
        )
        NotificationLog.objects.create(
            channel=channel, monitor_name="M2", status="failure", payload_sent={}
        )
        result = crud.list()
        assert result.count() == 2
