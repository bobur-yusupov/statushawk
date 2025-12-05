from typing import Dict, Any
from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "email", "first_name", "last_name", "password"]

        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data: Dict[Any, Any]) -> Any:
        return get_user_model().objects.create_user(**validated_data)
