from notifications.dtos import TelegramPayload


class TestTelegramPayload:
    def test_from_request_with_command(self) -> None:
        data: dict = {
            "message": {
                "text": "/start abc123token",
                "chat": {"id": 12345, "first_name": "John"},
            }
        }

        payload = TelegramPayload.from_request(data)

        assert payload.chat_id == "12345"
        assert payload.text == "/start abc123token"
        assert payload.user_name == "John"
        assert payload.is_command is True
        assert payload.token == "abc123token"

    def test_from_request_without_command(self) -> None:
        data: dict = {
            "message": {
                "text": "Hello bot",
                "chat": {"id": 67890, "first_name": "Jane"},
            }
        }

        payload = TelegramPayload.from_request(data)

        assert payload.chat_id == "67890"
        assert payload.text == "Hello bot"
        assert payload.user_name == "Jane"
        assert payload.is_command is False
        assert payload.token is None

    def test_from_request_start_without_token(self) -> None:
        data: dict = {
            "message": {"text": "/start", "chat": {"id": 111, "first_name": "Bob"}}
        }

        payload = TelegramPayload.from_request(data)

        assert payload.is_command is False
        assert payload.token is None

    def test_from_request_missing_first_name(self) -> None:
        data: dict = {"message": {"text": "Hi", "chat": {"id": 222}}}

        payload = TelegramPayload.from_request(data)

        assert payload.user_name == "User"

    def test_from_request_empty_message(self) -> None:
        data: dict = {"message": {}}

        payload = TelegramPayload.from_request(data)

        assert payload.chat_id == "None"
        assert payload.text == ""
        assert payload.user_name == "User"
        assert payload.is_command is False
