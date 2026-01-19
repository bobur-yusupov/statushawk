from typing import Dict, Any, Optional, List
from django.db.models import QuerySet, Avg
from django.utils import timezone
from datetime import timedelta, datetime
import logging
import statistics
from common.services import BaseService
from .models import Monitor, MonitorResult
from .crud import MonitorCRUD, MonitorResultCRUD
from notifications.tasks import send_notification_task
from notifications.crud import NotificationChannelCRUD

logger = logging.getLogger(__name__)


class MonitorService(BaseService[Monitor]):
    model = Monitor
    crud_class = MonitorCRUD

    def __init__(self) -> None:
        super().__init__()
        self.result_crud = MonitorResultCRUD()
        self.notification_crud = NotificationChannelCRUD()

    def process_check_result(
        self, monitor_id: int, is_up: bool, response_time: int, status_code: int
    ) -> None:
        """
        Called by the Runner Worker.
        Uses strictly existing fields: monitor.status (UP/DOWN string).
        """
        logger.info(
            f"Processing check result for monitor_id={monitor_id}, "
            f"is_up={is_up}, status_code={status_code}"
        )

        monitor = self.get(monitor_id)
        if not monitor:
            logger.error(f"Monitor {monitor_id} not found during result processing.")
            return

        # 1. Determine the New Status String based on the boolean result
        new_status = Monitor.StatusType.UP if is_up else Monitor.StatusType.DOWN

        # 2. Check for State Change (String Comparison)
        previous_status = monitor.status
        has_status_changed = (
            previous_status != new_status and new_status != Monitor.StatusType.PAUSED
        )

        self.result_crud.create(
            monitor=monitor,
            status_code=status_code,
            response_time_ms=response_time,
            is_up=is_up,
        )

        logger.debug(f"Logged result for {monitor.name}")

        self.update(monitor, status=new_status, last_checked_at=timezone.now())

        if has_status_changed:
            logger.info(
                f"Status changed ({previous_status} -> {new_status}) for {monitor.name}"
            )
            self.dispatch_alerts(monitor, new_status)
        elif is_up:
            self.detect_anomaly(monitor, response_time)

    def dispatch_alerts(self, monitor: Monitor, new_status: str) -> None:
        """
        Finds subscriber channels and pushes tasks to the Notification Queue.
        """
        try:
            channels = self.notification_crud.filter(
                user=monitor.user,
                is_active=True,
            )

            if not channels.exists():
                logger.warning(
                    f"No active notification channel for user {monitor.user.email}"
                )
                return

            subject, message = self._format_alert_message(monitor, new_status)

            for channel in channels:
                self._send_single_alert(
                    channel=channel, subject=subject, message=message
                )

        except Exception as e:
            logger.error(
                f"Failed to dispatch alerts for {monitor.name}: {e}", exc_info=True
            )

    def _send_single_alert(self, channel: Any, subject: str, message: str) -> None:
        try:
            logger.info(f"Queueing alert for channel {channel.id} ({channel.provider})")
            send_notification_task.apply_async(
                args=[channel.id, subject, message], queue="notification_queue"
            )
        except Exception as e:
            logger.error(f"Failed to queue task for channel {channel.id}: {e}")

    def _format_alert_message(
        self, monitor: Monitor, new_status: str
    ) -> tuple[str, str]:
        """Formatting logic for alerts."""
        is_up = new_status == Monitor.StatusType.UP
        icon = "🟢" if is_up else "🔴"

        subject = f"Alert: {monitor.name} is {new_status} {icon}"
        message = (
            f"Monitor: {monitor.name}\n"
            f"URL: {monitor.url}\n"
            f"Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"Status: {new_status} {icon}\n"
        )

        return subject, message

    def get_stats(self, monitor: Monitor, period: str = "24h") -> Dict[str, Any]:
        """Get aggregated statistics for a monitor."""
        start_time = self._calculate_start_time(period=period)

        qs = self.result_crud.filter_by_monitor_and_period(monitor, start_time)
        stats = self.result_crud.get_stats_aggregate(qs)
        last_check = self.result_crud.get_last_check(monitor=monitor)

        total = stats["total_checks"]
        up = stats["up_count"] or 0

        return {
            "period": period,
            "total_checks": total,
            "up_count": up,
            "down_count": stats["down_count"] or 0,
            "uptime_percentage": round((up / total * 100), 2) if total > 0 else 0.0,
            "avg_response_time": round(stats["avg_latency"] or 0, 2),
            "last_check": last_check,
        }

    def _calculate_start_time(self, period: str) -> datetime:
        now = timezone.now()
        if period == "7d":
            return now - timedelta(days=7)
        if period == "30d":
            return now - timedelta(days=30)
        return now - timedelta(hours=24)

    def get_history(
        self, monitor: Monitor, period: Optional[str] = None
    ) -> QuerySet[MonitorResult]:
        """Get history logs for a monitor."""
        return self.result_crud.get_history(monitor, period)

    def get_dashboard_stats(self, user: Any) -> Dict[str, Any]:
        """Get global dashboard statistics for a user."""
        active_monitors_qs = self.crud.filter(user=user, is_active=True)
        total_count = self.crud.filter(user=user).count()
        active_count = active_monitors_qs.count()

        down_count = active_monitors_qs.filter(status=Monitor.StatusType.DOWN).count()
        up_count = active_monitors_qs.filter(status=Monitor.StatusType.UP).count()

        last_24h = timezone.now() - timedelta(hours=24)
        latency_agg = self.result_crud.filter(
            monitor__user=user, created_at__gte=last_24h, response_time_ms__isnull=False
        ).aggregate(avg=Avg("response_time_ms"))

        avg_latency = latency_agg["avg"] or 0.0

        recent_failures = self._serialize_recent_failures(user)

        return {
            "total": total_count,
            "active": active_count,
            "up": up_count,
            "down": down_count,
            "avg_latency": round(avg_latency, 2),
            "recent_failures": recent_failures,
        }

    def _serialize_recent_failures(self, user: Any) -> List[Dict[str, Any]]:
        """Helper to fetch and format recent failures."""
        failures_qs = self.result_crud.get_recent_failures(user)
        return [
            {
                "id": res.id,
                "monitor_name": res.monitor.name,
                "url": res.monitor.url,
                "code": res.status_code,
                "created_at": res.created_at,
                "reason": (
                    "Timeout" if res.status_code == 0 else f"{res.status_code} Error"
                ),
            }
            for res in failures_qs
        ]

    def detect_anomaly(self, monitor: Monitor, current_response_time: int) -> None:
        """
        Calculates Z-Score to detect statistical outliers in response time.
        """
        history_values = list(
            self.result_crud.filter(monitor=monitor)
            .order_by("-created_at")
            .values_list("response_time_ms", flat=True)[:21]
        )

        if len(history_values) < 11:
            logger.debug(
                f"Not enough data for anomaly detection. Count: {len(history_values)}"
            )
            return

        baseline = [v for v in history_values[1:] if v is not None]

        if len(baseline) < 10:
            return

        try:
            mean = statistics.mean(baseline)
            stdev = statistics.stdev(baseline)
        except statistics.StatisticsError:
            return

        if stdev == 0:
            logger.warning(
                f"Variance is 0 (All values {mean}ms). Cannot calculate Z-score."
            )
            return

        z_score = (current_response_time - mean) / stdev

        if z_score > 3:
            logger.warning(f"ANOMALY CONFIRMED: Z-Score {z_score:.2f} > 3.0")
            logger.warning(
                f"Anomaly detected for {monitor.name}: {current_response_time}ms "
                f"(Avg: {mean:.0f}ms, Z-Score: {z_score:.2f})"
            )
            self._dispatch_anomaly_alert(monitor, current_response_time, mean)

    def _dispatch_anomaly_alert(
        self, monitor: Monitor, current: int, mean: float
    ) -> None:
        """Specific alert for performance degradation."""
        channels = self.notification_crud.filter(user=monitor.user, is_active=True)

        subject = f"Performance Warning: {monitor.name}"
        message = (
            f"Monitor: {monitor.name}\n"
            f"Current response: {current}ms\n"
            f"Average (Last 20 checks): {mean:.0f}ms\n"
            f"Analysis: Response time is abnormally high."
        )

        for channel in channels:
            self._send_single_alert(channel, subject, message)
