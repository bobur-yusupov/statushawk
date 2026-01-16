from rest_framework import serializers
from .models import NotificationChannel


class NotificationChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationChannel
        fields = ["id", "provider", "name", "created_at"]
