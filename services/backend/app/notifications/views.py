import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from .services import NotificationChannelService
from .serializers import NotificationChannelSerializer
from .dtos import TelegramPayload
from .utils import generate_telegram_link
from .models import NotificationChannel

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

            if reply_text:
                service.send_telegram_reply(payload.chat_id, reply_text)

        return Response({"status": "ok"})


class ChannelView(
    GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
):
    permission_classes = [IsAuthenticated]
    service_class = NotificationChannelService()
    serializer_class = NotificationChannelSerializer

    def get_queryset(self) -> QuerySet[NotificationChannel]:
        return self.service_class.list(user=self.request.user)

    def get(self, request: Request) -> Response:
        channels = self.service_class.list(
            user=request.user, filters={"is_active": True}
        )
        serializer = NotificationChannelSerializer(channels, many=True)
        return Response(serializer.data)


class TelegramLink(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        link = generate_telegram_link(request.user)

        return Response({"link": link})
