from typing import Any
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.serializers import BaseSerializer
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db.models import QuerySet
from .models import Monitor
from .serializers import (
    MonitorSerializer,
    MonitorHistorySerializer,
    MonitorStatsSerializer,
)
from .services import MonitorService


class MonitorPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "size"
    max_page_size = 100


class MonitorView(
    GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    serializer_class = MonitorSerializer
    pagination_class = MonitorPagination
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.service = MonitorService()

    def get_queryset(self) -> QuerySet[Monitor]:
        return self.service.list(user=self.request.user)  # type: ignore[misc]

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        serializer.save(user=self.request.user)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="period",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Time period for statistics",
                enum=["24h", "7d", "30d"],
                default="24h",
            )
        ],
        responses={200: MonitorStatsSerializer},
        description="Get aggregated statistics for a specific monitor",
    )
    @action(detail=True, methods=["get"])
    def stats(self, request: Request, pk: Any = None) -> Response:
        monitor = self.get_object()
        period = request.query_params.get("period", "24h")

        stats_data = self.service.get_stats(monitor, period)
        stats_data["last_check"] = (
            MonitorHistorySerializer(stats_data["last_check"]).data
            if stats_data["last_check"]
            else None
        )

        return Response(data=stats_data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="period",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Time period for history",
                enum=["24h", "7d", "30d"],
                required=False,
            )
        ],
        responses={200: MonitorHistorySerializer(many=True)},
        description="Get raw history logs for graphing with pagination support",
    )
    @action(detail=True, methods=["get"])
    def history(self, request: Request, pk: Any = None) -> Response:
        monitor = self.get_object()
        period = request.query_params.get("period")

        queryset = self.service.get_history(monitor, period)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MonitorHistorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MonitorHistorySerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        responses={
            200: OpenApiTypes.OBJECT,
        },
        description=(
            "Get global dashboard statistics including "
            "total uptime and recent incidents"
        ),
    )
    @action(detail=False, methods=["get"])
    def dashboard_stats(self, request: Request) -> Response:
        stats = self.service.get_dashboard_stats(request.user)  # type: ignore[misc]
        return Response(stats)
