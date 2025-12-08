from typing import Dict, Any
from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "email", "first_name", "last_name", "password"]

        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data: Dict[Any, Any]) -> Any:
        return get_user_model().objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """
    Serializer for LoginView
    """

    email = serializers.EmailField()
    password = serializers.CharField(
        style={
            "input_type": "password",
        },
        trim_whitespace=False,
    )

    def validate(self, attrs: Dict[Any, Any]) -> Dict[Any, Any]:
        email = attrs.get("email")
        password = attrs.get("password")
        user = authenticate(
            request=self.context.get("request"), username=email, password=password
        )

        if not user:
            message = "Unable to log in with provided credentials."
            raise serializers.ValidationError(message, code="authorization")

        attrs["user"] = user
        return attrs
