from typing import Dict, Any, Optional
from django.db.models import QuerySet
from django.utils import timezone
from datetime import timedelta
from common.services import BaseService
from .models import Monitor, MonitorResult
from .crud import MonitorCRUD, MonitorResultCRUD
from notifications.tasks import send_notification_task
from notifications.crud import NotificationChannelCRUD


class MonitorService(BaseService[Monitor]):
    model = Monitor
    crud_class = MonitorCRUD

    def __init__(self) -> None:
        super().__init__()
        self.result_crud = MonitorResultCRUD()

    def process_check_result(self, monitor_id: int, is_up: bool, response_time: int, status_code: int):
        """
        Called by the Runner Worker.
        Uses strictly existing fields: monitor.status (UP/DOWN string).
        """
        monitor = self.get(monitor_id)
        if not monitor:
            return

        # 1. Determine the New Status String based on the boolean result
        new_status = Monitor.StatusType.UP if is_up else Monitor.StatusType.DOWN
        
        # 2. Check for State Change (String Comparison)
        # We also treat PAUSED -> UP/DOWN as a change if you want, 
        # or just strictly check if it flipped UP <-> DOWN.
        previous_status = monitor.status
        status_changed = (previous_status != new_status) and (previous_status != Monitor.StatusType.PAUSED)

        # 3. Create the Result Record (Strictly following MonitorResult schema)
        MonitorResult.objects.create(
            monitor=monitor,
            status_code=status_code,
            response_time_ms=response_time,
            is_up=is_up
        )

        # 4. Update the Monitor (Strictly following Monitor schema)
        self.update(
            monitor, 
            status=new_status,
            last_checked_at=timezone.now()
        )

        # 5. Dispatch Alert if status changed
        if status_changed:
            self.dispatch_alerts(monitor, new_status)

    def dispatch_alerts(self, monitor: Monitor, is_up: bool):
        """
        Finds subscriber channels and pushes tasks to the Notification Queue.
        """
        # Fetch active channels for this user
        # (You could move this query to NotificationChannelCRUD if you want to be strict)
        # channels = NotificationChannel.objects.filter(
        #     user=monitor.user, 
        #     is_active=True
        # )

        channels = NotificationChannelCRUD.filter(
            user=monitor.user,
            is_active=True,
        )

        subject = f"Alert: {monitor.name} is {'UP 🟢' if is_up else 'DOWN 🔴'}"
        message = (
            f"Monitor: {monitor.name}\n"
            f"URL: {monitor.url}\n"
            f"Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"New Status: {subject}"
        )

        print(f"⚡ Publishing {len(channels)} alerts for {monitor.name}")

        for channel in channels:
            # 🚀 FIRE AND FORGET
            # This pushes a JSON message to RabbitMQ/Redis.
            # The 'notification_worker' will pick this up later.
            send_notification_task.delay(
                channel_id=channel.id,
                subject=subject,
                message=message
            )

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
