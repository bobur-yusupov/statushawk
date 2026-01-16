import pytest
from typing import Any
from unittest.mock import patch, MagicMock
from notifications.providers import ConsoleProvider, TelegramProvider


class TestConsoleProvider:
    @patch("sys.stdout")
    def test_send(self, mock_stdout: Any) -> None:
        provider = ConsoleProvider()
        provider.send({"test": "config"}, "Test Subject", "Test Message")
        mock_stdout.write.assert_called()
        call_args = mock_stdout.write.call_args[0][0]
        assert "Test Subject" in call_args
        assert "Test Message" in call_args


class TestTelegramProvider:
    @patch("notifications.providers.requests.post")
    @patch("notifications.providers.settings")
    def test_send_success(self, mock_settings: Any, mock_post: Any) -> None:
        mock_settings.TELEGRAM_BOT_TOKEN = "test_token"
        mock_settings.REQUEST_TIMEOUT = 10
        mock_response = MagicMock()
        mock_post.return_value = mock_response

        provider = TelegramProvider()
        provider.send({"chat_id": "123"}, "Subject", "Message")

        mock_post.assert_called_once()
        assert "bot" in mock_post.call_args[0][0]
        assert mock_post.call_args[1]["json"]["chat_id"] == "123"
        assert mock_post.call_args[1]["json"]["text"] == "Message"

    @patch("notifications.providers.settings")
    def test_send_missing_chat_id(self, mock_settings: Any) -> None:
        mock_settings.TELEGRAM_BOT_TOKEN = "test_token"
        provider = TelegramProvider()

        with pytest.raises(ValueError, match="Missing credentials"):
            provider.send({}, "Subject", "Message")

    @patch("notifications.providers.settings")
    def test_send_missing_token(self, mock_settings: Any) -> None:
        mock_settings.TELEGRAM_BOT_TOKEN = None
        provider = TelegramProvider()

        with pytest.raises(ValueError, match="Missing credentials"):
            provider.send({"chat_id": "123"}, "Subject", "Message")
