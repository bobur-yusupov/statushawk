from typing import Any
from django.core.management.base import BaseCommand
from django.utils import timezone
from monitor.models import Monitor
from monitor.tasks import check_monitor_task
import datetime


class Command(BaseCommand):
    help = "Restores monitoring loops that broke due to server restart."

    def handle(self, *args: Any, **options: Any) -> None:
        monitors = Monitor.objects.filter(is_active=True)
        restored_count = 0
        self.stdout.write(f"Checking {monitors.count()} monitors for stalled loops...")

        for monitor in monitors:
            should_run = False
            if not monitor.last_checked_at:
                should_run = True
            else:
                next_run_due = monitor.last_checked_at + datetime.timedelta(
                    seconds=monitor.interval
                )
                if next_run_due < timezone.now():
                    should_run = True

            if should_run:
                self.stdout.write(
                    f"Restarting loop for {monitor.name} (ID: {monitor.id})"
                )
                check_monitor_task.apply_async((monitor.id,), queue="runner_queue")
                restored_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully restored {restored_count} monitoring loops."
            )
        )
