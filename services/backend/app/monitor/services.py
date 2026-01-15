from typing import Dict, Any, Optional
from django.db.models import QuerySet
from django.utils import timezone
from datetime import timedelta
from common.services import BaseService
from .models import Monitor, MonitorResult
from .crud import MonitorCRUD, MonitorResultCRUD


class MonitorService(BaseService[Monitor]):
    model = Monitor
    crud_class = MonitorCRUD

    def __init__(self) -> None:
        super().__init__()
        self.result_crud = MonitorResultCRUD()

    def get_stats(self, monitor: Monitor, period: str = "24h") -> Dict[str, Any]:
        """Get aggregated statistics for a monitor."""
        now = timezone.now()

        if period == "7d":
            start_time = now - timedelta(days=7)
        elif period == "30d":
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(hours=24)

        qs = self.result_crud.filter_by_monitor_and_period(monitor, start_time)
        stats = self.result_crud.get_stats_aggregate(qs)

        total = stats["total_checks"]
        up = stats["up_count"] or 0
        uptime = (up / total * 100) if total > 0 else 0.0
        last_check = self.result_crud.get_last_check(monitor)

        return {
            "period": period,
            "total_checks": total,
            "up_count": up,
            "down_count": stats["down_count"] or 0,
            "uptime_percentage": round(uptime, 2),
            "avg_response_time": round(stats["avg_latency"] or 0, 2),
            "last_check": last_check,
        }

    def get_history(
        self, monitor: Monitor, period: Optional[str] = None
    ) -> QuerySet[MonitorResult]:
        """Get history logs for a monitor."""
        return self.result_crud.get_history(monitor, period)

    def get_dashboard_stats(self, user: Any) -> Dict[str, Any]:
        """Get global dashboard statistics for a user."""
        monitor_crud = MonitorCRUD()
        total_monitors = monitor_crud.count_by_user(user)
        active_monitors = monitor_crud.count_by_user(user, is_active=True)

        down_count = 0
        total_latency = 0.0
        latency_count = 0

        for m in monitor_crud.filter_by_user(user, is_active=True):
            last = self.result_crud.get_last_check(m)
            if last:
                if not last.is_up:
                    down_count += 1
                if last.response_time_ms is not None:
                    total_latency += last.response_time_ms
                    latency_count += 1

        avg_latency = (total_latency / latency_count) if latency_count > 0 else 0.0
        up_count = active_monitors - down_count

        recent_failures_qs = self.result_crud.get_recent_failures(user)

        recent_failures = []
        for res in recent_failures_qs:
            recent_failures.append(
                {
                    "id": res.id,
                    "monitor_name": res.monitor.name,
                    "url": res.monitor.url,
                    "code": res.status_code,
                    "created_at": res.created_at,
                    "reason": (
                        "Timeout"
                        if res.status_code == 0
                        else f"{res.status_code} Error"
                    ),
                }
            )

        return {
            "total": total_monitors,
            "active": active_monitors,
            "up": up_count,
            "down": down_count,
            "avg_latency": round(avg_latency, 2),
            "recent_failures": recent_failures,
        }
