import requests
import sys
from django.conf import settings
from abc import ABC, abstractmethod


class BaseProvider(ABC):
    @abstractmethod
    def send(self, config: dict, subject: str, message: str) -> None:
        pass


class ConsoleProvider(BaseProvider):
    def send(self, config: dict, subject: str, message: str) -> None:
        output = (
            f"\n"
            f"\n======== [DEBUG NOTIFICATION] ========\n"
            f"Subject: {subject}\n"
            f"Message: {message}\n"
            f"Config: {config} \n"
            f"========================================\n"
        )
        sys.stdout.write(output)
        sys.stdout.flush()


class TelegramProvider(BaseProvider):
    def send(self, config: dict, subject: str, message: str) -> None:
        chat_id = config.get("chat_id")
        token = settings.TELEGRAM_BOT_TOKEN
        if not chat_id or not token:
            raise ValueError("Missing credentials")

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(
            url,
            json={"chat_id": chat_id, "text": message},
            timeout=settings.REQUEST_TIMEOUT,
        ).raise_for_status()


PROVIDER_MAP = {"telegram": TelegramProvider(), "console": ConsoleProvider()}
