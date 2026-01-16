from typing import Any
import requests
import time
import logging
from celery import shared_task
from .models import Monitor
from .services import MonitorService

logger = logging.getLogger(__name__)


@shared_task(
    name="monitor.tasks.check_monitor_task",
    bind=True,
    queue="runner_queue",
    acks_late=True,
    reject_on_worker_lost=True,
)
def check_monitor_task(self: Any, monitor_id: int) -> str:
    logger.info(f"Starting check for monitor_id={monitor_id}")

    try:
        monitor = Monitor.objects.only("url", "interval", "is_active").get(
            id=monitor_id
        )
        if not monitor.is_active:
            logger.info(f"Monitor {monitor_id} is inactive, stopping loop")
            return f"Monitor {monitor_id} is inactive. Loop stopping..."

    except Monitor.DoesNotExist:
        logger.error(f"Monitor {monitor_id} does not exist")
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
        logger.info(
            f"Monitor {monitor.url} responded "
            f"with status_code={status_code}, is_up={is_up}"
        )

    except requests.RequestException as e:
        status_code = 0
        is_up = False
        logger.warning(f"Monitor {monitor.url} failed with exception: {e}")

    duration_ms = int((time.time() - start_time) * 1000)
    logger.debug(f"Check completed in {duration_ms}ms")

    # Use MonitorService to process the result (handles alerts)
    service = MonitorService()
    service.process_check_result(monitor_id, is_up, duration_ms, status_code)

    # Schedule next check
    check_monitor_task.apply_async((monitor_id,), countdown=monitor.interval)
    logger.info(f"Next check for {monitor.url} scheduled in {monitor.interval}s")

    return f"Checked {monitor.url}: {status_code} (Next in {monitor.interval}s)"
