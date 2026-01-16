import pytest
import time
from typing import Any
from unittest.mock import patch
from django.contrib.auth import get_user_model
from faker import Faker
from notifications.utils import generate_telegram_link, verify_telegram_token

User = get_user_model()
fake = Faker()


@pytest.fixture
def user() -> Any:
    return User.objects.create_user(
        email=fake.email(), password="testpass123"
    )  # type: ignore[attr-defined]


@pytest.mark.django_db
class TestTelegramUtils:
    @patch("notifications.utils.settings")
    def test_generate_telegram_link(self, mock_settings: Any, user: Any) -> None:
        mock_settings.SECRET_KEY = "test_secret_key"
        mock_settings.TELEGRAM_BOT_NAME = "test_bot"

        link = generate_telegram_link(user)

        assert link.startswith("https://t.me/test_bot?start=")
        assert len(link) > 30

    @patch("notifications.utils.settings")
    def test_verify_telegram_token_valid(self, mock_settings: Any, user: Any) -> None:
        mock_settings.SECRET_KEY = "test_secret_key"
        mock_settings.TELEGRAM_BOT_NAME = "test_bot"

        link = generate_telegram_link(user)
        token = link.split("start=")[1]

        result = verify_telegram_token(token)

        assert result == user.id

    @patch("notifications.utils.settings")
    def test_verify_telegram_token_expired(self, mock_settings: Any, user: Any) -> None:
        mock_settings.SECRET_KEY = "test_secret_key"
        mock_settings.TELEGRAM_BOT_NAME = "test_bot"

        link = generate_telegram_link(user)
        token = link.split("start=")[1]

        time.sleep(1)
        result = verify_telegram_token(token, max_age=0)

        assert result is None

    @patch("notifications.utils.settings")
    def test_verify_telegram_token_invalid(self, mock_settings: Any) -> None:
        mock_settings.SECRET_KEY = "test_secret_key"

        result = verify_telegram_token("invalid_token")

        assert result is None

    @patch("notifications.utils.settings")
    def test_verify_telegram_token_tampered(
        self, mock_settings: Any, user: Any
    ) -> None:
        mock_settings.SECRET_KEY = "test_secret_key"
        mock_settings.TELEGRAM_BOT_NAME = "test_bot"

        link = generate_telegram_link(user)
        token = link.split("start=")[1]
        tampered_token = token[:-5] + "XXXXX"

        result = verify_telegram_token(tampered_token)

        assert result is None

    @patch("notifications.utils.settings")
    def test_verify_telegram_token_short(self, mock_settings: Any) -> None:
        mock_settings.SECRET_KEY = "test_secret_key"

        result = verify_telegram_token("abc")

        assert result is None
