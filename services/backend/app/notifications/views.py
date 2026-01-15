import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from .utils import verify_telegram_token
from .models import NotificationChannel
from .services import NotificationChannelService

User = get_user_model()

class TelegramWebhookView(APIView):
    """
    Telegram sends updates here. We look for '/start <token>' messages.
    """
    permission_classes = [AllowAny] # Telegram servers are not logged in users

    def post(self, request):
        data = request.data
        
        # 1. Extract the message
        message = data.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")

        print("Received Telegram message:", text, "from chat_id:", chat_id)
        
        if not text or not chat_id:
            return Response({"status": "ignored"})

        # 2. Check if it is a Deep Link command: "/start <token>"
        if text.startswith("/start") and " " in text:
            token = text.split(" ")[1] # Get the second part
            
            # 3. Verify the Token
            user_id = verify_telegram_token(token)
            print(user_id)
            if not user_id:
                self._send_reply(chat_id, "❌ This link is expired or invalid. Please try again from the dashboard.")
                return Response({"status": "invalid_token"})

            # 4. Link the User!
            try:
                user = User.objects.get(id=user_id)
                
                # Check if already exists to prevent duplicates
                channel, created = NotificationChannel.objects.get_or_create(
                    user=user,
                    provider="telegram",
                    config__chat_id=str(chat_id),
                    defaults={
                        "name": f"Telegram ({message.get('chat', {}).get('first_name', 'User')})",
                        "config": {"chat_id": str(chat_id)}
                    }
                )
                
                if created:
                    self._send_reply(chat_id, f"✅ Connected to StatusHawk! Hello {user.first_name}.")
                else:
                    self._send_reply(chat_id, "ℹ️ You are already connected.")
                    
            except User.DoesNotExist:
                pass
        
        else:
            self._send_reply(chat_id, "ℹ️ Send there is a problem with your notification setup.")

        return Response({"status": "ok"})

    def _send_reply(self, chat_id, text):
        # Re-use our service logic to send the reply
        # We construct a temporary config just to reply
        service = NotificationChannelService()
        service._send_telegram({"chat_id": chat_id}, text)