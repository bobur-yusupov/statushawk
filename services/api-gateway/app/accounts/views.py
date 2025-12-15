from typing import Type, Any, Optional, Union, Dict
from django.http import HttpRequest
from rest_framework.generics import CreateAPIView
from rest_framework.serializers import Serializer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.parsers import JSONParser
from rest_framework import status, permissions, views, authentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from common.utils import generate_timestamp_iso
from utils.logger import log_info, log_warning
from .serializers import UserSerializer, LoginSerializer


class AuthThrottle(SimpleRateThrottle):
    scope = "signup"

    rate = "5/min"

    def get_cache_key(self, request: Request, view: Any) -> Optional[str]:
        ident: Union[int, str]
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {"scope": self.scope, "ident": ident}


class SignUpView(CreateAPIView):
    serializer_class: Type[Serializer] = UserSerializer
    http_method_names = ["post"]
    throttle_classes = [AuthThrottle]
    parser_classes = [JSONParser]
    permission_classes = [permissions.AllowAny]

    def http_method_not_allowed(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> Response:
        log_warning(f"Method not allowed on SignUp", method=request.method, ip=request.META.get('REMOTE_ADDR'))

        return Response(
            data={
                "status": "error",
                "timestamp": generate_timestamp_iso(),
                "data": {
                    "message": "Method not allowed.",
                },
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        email = request.data.get("email")
        log_info("New signup attempt", email=email)
        
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            log_info("User registered successfully", user_id=user.id, email=email)

            return Response(
                data={
                    "status": "ok",
                    "timestamp": generate_timestamp_iso(),
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        log_warning("Signup validation failed", email=email, errors=serializer.errors)            

        return Response(
            data={
                "status": "error",
                "timestamp": generate_timestamp_iso(),
                "data": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class LoginView(ObtainAuthToken):
    throttle_classes = [AuthThrottle]
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser]
    http_method_names = ["post"]
    serializer_class: Type[Serializer] = LoginSerializer

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        email_attempt = request.data.get("email")
        log_info("New login attempt", email=email_attempt)
        
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            log_warning("Login failed: Invalid credentials", email=email_attempt, errors=serializer.errors)

            return Response(
                data={
                    "status": "error",
                    "timestamp": generate_timestamp_iso(),
                    "data": None,
                    "error": serializer.errors,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)

        log_info("User logged in successfully", user_id=user.id, email=email_attempt)

        response_data: Dict[str, Any] = {
            "status": "ok",
            "timestamp": generate_timestamp_iso(),
            "data": {"token": token.key},
        }

        return Response(data=response_data, status=status.HTTP_201_CREATED)


class LogoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [authentication.TokenAuthentication]

    def post(self, request: Request) -> Response:
        if request.auth:
            request.auth.delete()

        log_info("User logged out successfully", user_id=request.user.id)
        
        message = "Successfully logged out."
        return Response(
            data={
                "status": "ok",
                "timestamp": generate_timestamp_iso(),
                "data": {
                    "message": message,
                },
            },
            status=status.HTTP_200_OK,
        )
