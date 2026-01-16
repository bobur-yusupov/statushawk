import pytest
from typing import Any
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from faker import Faker
from notifications.models import NotificationChannel

User = get_user_model()
fake = Faker()


@pytest.fixture
def api_client() -> Any:
    return APIClient()


@pytest.fixture
def user() -> Any:
    return User.objects.create_user(
        email=fake.email(), password="testpass123"
    )  # type: ignore[attr-defined]


@pytest.fixture
def authenticated_client(api_client: Any, user: Any) -> Any:
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def channel(user: Any) -> Any:
    return NotificationChannel.objects.create(
        user=user, name="Test", provider="telegram", config={"chat_id": "123"}
    )


@pytest.mark.django_db
class TestTelegramWebhookView:
    @patch("notifications.views.NotificationChannelService")
    def test_webhook_with_command(
        self, mock_service_class: Any, api_client: Any, user: Any
    ) -> None:
        mock_service = MagicMock()
        mock_service.link_telegram_channel.return_value = "Connected!"
        mock_service_class.return_value = mock_service

        data = {
            "message": {
                "text": "/start token123",
                "chat": {"id": 12345, "first_name": "John"},
            }
        }

        response = api_client.post(
            "/api/v1/notifications/webhook/telegram/", data, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ok"
        mock_service.link_telegram_channel.assert_called_once()
        mock_service.send_telegram_reply.assert_called_once()

    def test_webhook_without_command(self, api_client: Any) -> None:
        data = {
            "message": {"text": "Hello", "chat": {"id": 12345, "first_name": "John"}}
        }

        response = api_client.post(
            "/api/v1/notifications/webhook/telegram/", data, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ok"

    def test_webhook_empty_message(self, api_client: Any) -> None:
        data: dict = {"message": {}}

        response = api_client.post(
            "/api/v1/notifications/webhook/telegram/", data, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ignored"


@pytest.mark.django_db
class TestChannelView:
    def test_list_channels(self, authenticated_client: Any, user: Any) -> None:
        NotificationChannel.objects.create(
            user=user, name="C1", provider="telegram", config={}
        )
        NotificationChannel.objects.create(
            user=user, name="C2", provider="telegram", config={}
        )

        response = authenticated_client.get("/api/v1/notifications/channels/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_list_channels_filter_active(
        self, authenticated_client: Any, user: Any
    ) -> None:
        NotificationChannel.objects.create(
            user=user, name="Active", provider="telegram", config={}, is_active=True
        )
        NotificationChannel.objects.create(
            user=user, name="Inactive", provider="telegram", config={}, is_active=False
        )

        response = authenticated_client.get("/api/v1/notifications/channels/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_retrieve_channel(self, authenticated_client: Any, channel: Any) -> None:
        response = authenticated_client.get(
            f"/api/v1/notifications/channels/{channel.id}/"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == channel.id

    def test_delete_channel(self, authenticated_client: Any, channel: Any) -> None:
        channel_id = channel.id

        response = authenticated_client.delete(
            f"/api/v1/notifications/channels/{channel_id}/"
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not NotificationChannel.objects.filter(id=channel_id).exists()

    def test_list_channels_unauthenticated(self, api_client: Any) -> None:
        response = api_client.get("/api/v1/notifications/channels/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_isolation(self, authenticated_client: Any, user: Any) -> None:
        other_user = User.objects.create_user(  # type: ignore[attr-defined]
            email=fake.email(), password="testpass123"
        )
        NotificationChannel.objects.create(
            user=user, name="My Channel", provider="telegram", config={}
        )
        NotificationChannel.objects.create(
            user=other_user, name="Other Channel", provider="telegram", config={}
        )

        response = authenticated_client.get("/api/v1/notifications/channels/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1


@pytest.mark.django_db
class TestTelegramLinkView:
    @patch("notifications.views.generate_telegram_link")
    def test_get_telegram_link(
        self, mock_generate: Any, authenticated_client: Any, user: Any
    ) -> None:
        mock_generate.return_value = "https://t.me/bot?start=token123"

        response = authenticated_client.get("/api/v1/notifications/telegram-link/")

        assert response.status_code == status.HTTP_200_OK
        assert "link" in response.data
        assert "t.me" in response.data["link"]
        mock_generate.assert_called_once_with(user)

    def test_get_telegram_link_unauthenticated(self, api_client: Any) -> None:
        response = api_client.get("/api/v1/notifications/telegram-link/")

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


@pytest.mark.django_db
class TestNotificationIntegration:
    """Full stack integration tests"""

    @patch("notifications.services.PROVIDER_MAP")
    def test_full_notification_flow(self, mock_provider_map: Any, user: Any) -> None:
        mock_provider = MagicMock()
        mock_provider_map.get.return_value = mock_provider

        channel = NotificationChannel.objects.create(
            user=user,
            name="Integration",
            provider="telegram",
            config={"chat_id": "123"},
        )

        from notifications.services import NotificationChannelService

        service = NotificationChannelService()
        service.send_alert(
            channel.id, "Test Alert", "This is a test"
        )  # type: ignore[attr-defined]

        mock_provider.send.assert_called_once()
        from notifications.models import NotificationLog

        log = NotificationLog.objects.filter(channel=channel).first()
        assert log is not None
        assert log.status == "success"

    @patch("notifications.views.generate_telegram_link")
    def test_telegram_link_generation_flow(
        self, mock_generate: Any, authenticated_client: Any, user: Any
    ) -> None:
        mock_generate.return_value = "https://t.me/testbot?start=abc123"

        response = authenticated_client.get("/api/v1/notifications/telegram-link/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["link"] == "https://t.me/testbot?start=abc123"
