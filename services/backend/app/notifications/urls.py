from django.urls import path
from .views import TelegramWebhookView

urlpatterns = [
    path('webhook/telegram/', TelegramWebhookView.as_view(), name='telegram-webhook'),
]