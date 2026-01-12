import requests
import time
from celery import shared_task
from django.utils import timezone
from .models import Monitor, MonitorResult


@shared_task(name="monitor.tasks.check_monitor_task", bind=True)
def check_monitor_task(self, monitor_id: int) -> str:
    try:
        monitor = Monitor.objects.only("url", "interval", "is_active").get(
            id=monitor_id
        )
        if not monitor.is_active:
            return f"Monitor {monitor_id} is inactive. Loop stopping..."

    except Monitor.DoesNotExist:
        return f"Monitor {monitor_id} does not exist. Loop stopping..."

    start_time = time.time()
    try:
        response = requests.get(
            monitor.url,
            timeout=10,
            headers={"User-Agent": "StatusHawk Monitor/1.0"},
        )
        status_code = response.status_code
        is_up = 200 <= status_code < 300

    except requests.RequestException:
        status_code = 0
        is_up = False

    duration_ms = int((time.time() - start_time) * 1000)

    MonitorResult.objects.create(
        monitor=monitor,
        status_code=status_code,
        response_time_ms=duration_ms,
        is_up=is_up,
    )

    monitor.status = "UP" if is_up else "DOWN"
    monitor.last_checked_at = timezone.now()
    monitor.save(update_fields=["status", "last_checked_at"])

    check_monitor_task.apply_async((monitor_id,), countdown=monitor.interval)
    return f"Checked {monitor.url}: {status_code} (Next in {monitor.interval}s)"
