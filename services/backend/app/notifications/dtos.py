from typing import Optional
from dataclasses import dataclass


@dataclass
class TelegramPayload:
    """Encapsulates the raw webhook data."""

    chat_id: str
    text: str
    user_name: str
    is_command: bool
    token: Optional[str]

    @classmethod
    def from_request(cls, data: dict) -> "TelegramPayload":
        msg: dict = data.get("message", {})
        text: str = msg.get("text", "")
        chat = msg.get("chat", {})

        is_command = text.startswith("/start") and len(text.split(" ")) > 1
        token = text.split(" ")[1] if is_command else None

        return cls(
            chat_id=str(chat.get("id")),
            text=text,
            user_name=chat.get("first_name", "User"),
            is_command=is_command,
            token=token,
        )
