from typing import Type, Any, Optional, Union
from django.http import HttpRequest
from rest_framework.generics import CreateAPIView
from rest_framework.serializers import Serializer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.parsers import JSONParser
from rest_framework import status, permissions
from .serializers import UserSerializer


class SignUpThrottle(SimpleRateThrottle):
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
    throttle_classes = [SignUpThrottle]
    parser_classes = [JSONParser]
    permission_classes = [permissions.AllowAny]

    def http_method_not_allowed(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> Response:
        return Response(
            data={
                "status": "error",
                "data": {
                    "message": "Method not allowed.",
                },
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response(
                data={"status": "ok", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )

        return Response(
            data={"status": "error", "data": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
