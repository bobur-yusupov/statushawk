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
from django.db.models import QuerySet, Avg, Count, Case, When, IntegerField
from django.utils import timezone
from datetime import timedelta
from .models import Monitor, MonitorResult
from .serializers import (
    MonitorSerializer,
    MonitorHistorySerializer,
    MonitorStatsSerializer,
)


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

    def get_queryset(self) -> QuerySet[Monitor]:
        return Monitor.objects.filter(user=self.request.user)  # type: ignore[misc]

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
        """
        Get aggregated statistics for a specific monitor.
        Query Params: ?period=24h (default), 7d, 30d
        """
        monitor = self.get_object()
        period_param = request.query_params.get("period", "24h")
        now = timezone.now()

        if period_param == "7d":
            start_time = now - timedelta(days=7)
        elif period_param == "30d":
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(hours=24)

        qs = monitor.results.filter(created_at__gt=start_time)

        stats = qs.aggregate(
            total_checks=Count("id"),
            up_count=Count(Case(When(is_up=True, then=1), output_field=IntegerField())),
            down_count=Count(
                Case(When(is_up=False, then=1), output_field=IntegerField())
            ),
            avg_latency=Avg("response_time_ms"),
        )

        total = stats["total_checks"]
        up = stats["up_count"] or 0
        uptime = (up / total * 100) if total > 0 else 0.0
        last_check = monitor.results.order_by("-created_at").first()

        data = {
            "period": period_param,
            "total_checks": total,
            "up_count": up,
            "down_count": stats["down_count"] or 0,
            "uptime_percentage": round(uptime, 2),
            "avg_response_time": round(stats["avg_latency"] or 0, 2),
            "last_check": (
                MonitorHistorySerializer(last_check).data if last_check else None
            ),
        }

        return Response(data=data)

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
        """
        Get raw history logs for graphing.
        Pagination is enabled by default via settings.
        """
        monitor = self.get_object()

        # Optimize: Only fetch fields needed for the graph
        queryset = monitor.results.all().order_by("-created_at")

        # Optional: Filter by period here too
        period_param = request.query_params.get("period")
        if period_param == "24h":
            queryset = queryset.filter(
                created_at__gte=timezone.now() - timedelta(hours=24)
            )

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
        description="Get global dashboard statistics including total uptime and recent incidents",
    )
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request: Request) -> Response:
        user_monitors = Monitor.objects.filter(user=request.user)

        total_monitors = user_monitors.count()
        active_monitors = user_monitors.filter(is_active=True).count()

        down_count = 0
        total_latency = 0.0
        latency_count = 0

        for m in user_monitors.filter(is_active=True):
            last = m.results.order_by('-created_at').first()
            if last:
                if not last.is_up:
                    down_count += 1
                if last.response_time_ms is not None:
                    total_latency += last.response_time_ms
                    latency_count += 1
        
        avg_latency = (total_latency / latency_count) if latency_count > 0 else 0.0
        up_count = active_monitors - down_count

        recent_failures_qs = (
            MonitorResult.objects.filter(monitor__user=request.user, is_up=False)
            .select_related('monitor')
            .order_by('-created_at')[:5]
        )

        recent_failures = []
        for res in recent_failures_qs:
            recent_failures.append({
                "id": res.id,
                "monitor_name": res.monitor.name,
                "url": res.monitor.url,
                "code": res.status_code,
                "created_at": res.created_at,
                "reason": "Timeout" if res.status_code == 0 else f"{res.status_code} Error"
            })

        return Response({
            "total": total_monitors,
            "active": active_monitors,
            "up": up_count,
            "down": down_count,
            "avg_latency": round(avg_latency, 2),
            "recent_failures": recent_failures
        })
