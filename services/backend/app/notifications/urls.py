from django.urls import path
from .views import TelegramWebhookView, ChannelView, TelegramLink
from django.urls import include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("channels", ChannelView, basename="channels")

urlpatterns = [
    path("webhook/telegram/", TelegramWebhookView.as_view(), name="telegram-webhook"),
    path("telegram-link/", TelegramLink.as_view(), name="telegram-link"),
    path("", include(router.urls)),
]
