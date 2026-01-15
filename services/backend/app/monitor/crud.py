from typing import Optional, Dict, Any
from django.db.models import QuerySet, Avg, Count, Case, When, IntegerField
from datetime import datetime, timedelta
from django.utils import timezone
from common.crud import FullCRUD
from .models import Monitor, MonitorResult


class MonitorResultCRUD(FullCRUD[MonitorResult]):
    model = MonitorResult

    def filter_by_monitor_and_period(
        self, monitor: Monitor, start_time: datetime
    ) -> QuerySet[MonitorResult]:
        return self.model.objects.filter(  # type: ignore[attr-defined]
            monitor=monitor, created_at__gt=start_time
        )

    def get_stats_aggregate(
        self, queryset: QuerySet[MonitorResult]
    ) -> Dict[str, Any]:
        return queryset.aggregate(
            total_checks=Count("id"),
            up_count=Count(
                Case(When(is_up=True, then=1), output_field=IntegerField())
            ),
            down_count=Count(
                Case(When(is_up=False, then=1), output_field=IntegerField())
            ),
            avg_latency=Avg("response_time_ms"),
        )

    def get_last_check(self, monitor: Monitor) -> Optional[MonitorResult]:
        return (  # type: ignore[attr-defined]
            self.model.objects.filter(monitor=monitor)
            .order_by("-created_at")
            .first()
        )

    def get_history(
        self, monitor: Monitor, period: Optional[str] = None
    ) -> QuerySet[MonitorResult]:
        queryset = self.model.objects.filter(  # type: ignore[attr-defined]
            monitor=monitor
        ).order_by("-created_at")

        if period == "24h":
            queryset = queryset.filter(
                created_at__gte=timezone.now() - timedelta(hours=24)
            )

        return queryset

    def get_recent_failures(
        self, user: Any, limit: int = 5
    ) -> QuerySet[MonitorResult]:
        return (  # type: ignore[attr-defined]
            self.model.objects.filter(monitor__user=user, is_up=False)
            .select_related("monitor")
            .order_by("-created_at")[:limit]
        )


class MonitorCRUD(FullCRUD[Monitor]):
    model = Monitor

    def filter_by_user(
        self, user: Any, is_active: Optional[bool] = None
    ) -> QuerySet[Monitor]:
        queryset = self.model.objects.filter(  # type: ignore[attr-defined]
            user=user
        )
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
        return queryset

    def count_by_user(self, user: Any, is_active: Optional[bool] = None) -> int:
        return self.filter_by_user(user, is_active).count()
