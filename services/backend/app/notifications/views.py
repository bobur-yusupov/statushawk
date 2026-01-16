import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model

from .services import NotificationChannelService
from .dtos import TelegramPayload

logger = logging.getLogger(__name__)
User = get_user_model()


class TelegramWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        payload = TelegramPayload.from_request(request.data)
        if not payload.chat_id or not payload.text:
            return Response({"status": "ignored"})

        if payload.is_command and payload.token:
            service = NotificationChannelService()

            reply_text = service.link_telegram_channel(
                token=payload.token,
                chat_id=payload.chat_id,
                user_name=payload.user_name,
            )

            service.send_telegram_reply(payload.chat_id, reply_text)

        return Response({"status": "ok"})
