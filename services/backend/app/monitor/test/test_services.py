import pytest
from typing import Any
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from faker import Faker
from monitor.models import Monitor, MonitorResult
from monitor.services import MonitorService

User = get_user_model()
fake = Faker()


@pytest.fixture
def user() -> Any:
    return User.objects.create_user(email=fake.email(), password="testpass123")


@pytest.fixture
def monitor(user: Any) -> Monitor:
    return Monitor.objects.create(
        user=user, name=fake.company(), url=fake.url(), monitor_type="HTTP"
    )


@pytest.fixture
def service() -> MonitorService:
    return MonitorService()


@pytest.mark.django_db
class TestMonitorService:

    def test_create(self, service: MonitorService, user: Any) -> None:
        monitor = service.create(
            user=user, name="Test", url="https://test.com", monitor_type="HTTP"
        )
        assert monitor.id is not None
        assert monitor.user == user

    def test_get(self, service: MonitorService, monitor: Monitor, user: Any) -> None:
        result = service.get(id=monitor.id, user=user)
        assert result.id == monitor.id

    def test_list(self, service: MonitorService, user: Any) -> None:
        Monitor.objects.create(
            user=user, name="M1", url=fake.url(), monitor_type="HTTP"
        )
        Monitor.objects.create(
            user=user, name="M2", url=fake.url(), monitor_type="HTTP"
        )

        result = service.list(user=user)
        assert result.count() == 2

    def test_update(self, service: MonitorService, monitor: Monitor) -> None:
        updated = service.update(monitor, name="Updated")
        assert updated.name == "Updated"

    def test_delete(self, service: MonitorService, monitor: Monitor) -> None:
        monitor_id = monitor.id
        service.delete(monitor)
        assert not Monitor.objects.filter(id=monitor_id).exists()

    def test_get_stats_24h(self, service: MonitorService, monitor: Monitor) -> None:
        now = timezone.now()
        for i in range(5):
            MonitorResult.objects.create(
                monitor=monitor,
                status_code=200,
                response_time_ms=100,
                is_up=True,
                created_at=now - timedelta(hours=i),
            )

        stats = service.get_stats(monitor, period="24h")
        assert stats["period"] == "24h"
        assert stats["total_checks"] == 5
        assert stats["uptime_percentage"] == 100.0

    def test_get_stats_with_failures(
        self, service: MonitorService, monitor: Monitor
    ) -> None:
        MonitorResult.objects.create(
            monitor=monitor, status_code=200, response_time_ms=100, is_up=True
        )
        MonitorResult.objects.create(
            monitor=monitor, status_code=500, response_time_ms=200, is_up=False
        )

        stats = service.get_stats(monitor, period="24h")
        assert stats["total_checks"] == 2
        assert stats["up_count"] == 1
        assert stats["down_count"] == 1
        assert stats["uptime_percentage"] == 50.0

    def test_get_stats_7d(self, service: MonitorService, monitor: Monitor) -> None:
        now = timezone.now()
        for i in range(3):
            MonitorResult.objects.create(
                monitor=monitor,
                status_code=200,
                response_time_ms=150,
                is_up=True,
                created_at=now - timedelta(days=i),
            )

        stats = service.get_stats(monitor, period="7d")
        assert stats["period"] == "7d"
        assert stats["total_checks"] == 3

    def test_get_stats_30d(self, service: MonitorService, monitor: Monitor) -> None:
        now = timezone.now()
        for i in range(10):
            MonitorResult.objects.create(
                monitor=monitor,
                status_code=200,
                response_time_ms=100,
                is_up=True,
                created_at=now - timedelta(days=i),
            )

        stats = service.get_stats(monitor, period="30d")
        assert stats["period"] == "30d"
        assert stats["total_checks"] == 10

    def test_get_stats_no_results(
        self, service: MonitorService, monitor: Monitor
    ) -> None:
        stats = service.get_stats(monitor)
        assert stats["total_checks"] == 0
        assert stats["uptime_percentage"] == 0.0
        assert stats["last_check"] is None

    def test_get_history(self, service: MonitorService, monitor: Monitor) -> None:
        for i in range(3):
            MonitorResult.objects.create(
                monitor=monitor, status_code=200, response_time_ms=100, is_up=True
            )

        history = service.get_history(monitor)
        assert history.count() == 3

    def test_get_history_with_period(
        self, service: MonitorService, monitor: Monitor
    ) -> None:
        now = timezone.now()
        result1 = MonitorResult.objects.create(
            monitor=monitor, status_code=200, response_time_ms=100, is_up=True
        )
        result1.created_at = now - timedelta(hours=12)
        result1.save()

        result2 = MonitorResult.objects.create(
            monitor=monitor, status_code=200, response_time_ms=100, is_up=True
        )
        result2.created_at = now - timedelta(days=2)
        result2.save()

        history = service.get_history(monitor, period="24h")
        assert history.count() == 1

    def test_get_dashboard_stats(self, service: MonitorService, user: Any) -> None:
        m1 = Monitor.objects.create(
            user=user, name="M1", url=fake.url(), monitor_type="HTTP", is_active=True
        )
        m2 = Monitor.objects.create(
            user=user, name="M2", url=fake.url(), monitor_type="HTTP", is_active=True
        )

        MonitorResult.objects.create(
            monitor=m1, status_code=200, response_time_ms=100, is_up=True
        )
        MonitorResult.objects.create(
            monitor=m2, status_code=500, response_time_ms=200, is_up=False
        )

        stats = service.get_dashboard_stats(user)
        assert stats["total"] == 2
        assert stats["active"] == 2
        assert stats["up"] == 1
        assert stats["down"] == 1
        assert stats["avg_latency"] == 150.0

    def test_get_dashboard_stats_recent_failures(
        self, service: MonitorService, user: Any, monitor: Monitor
    ) -> None:
        for i in range(3):
            MonitorResult.objects.create(
                monitor=monitor, status_code=500, response_time_ms=100, is_up=False
            )

        stats = service.get_dashboard_stats(user)
        assert len(stats["recent_failures"]) == 3
        assert stats["recent_failures"][0]["monitor_name"] == monitor.name

    def test_get_dashboard_stats_inactive_monitors(
        self, service: MonitorService, user: Any
    ) -> None:
        Monitor.objects.create(
            user=user, name="M1", url=fake.url(), monitor_type="HTTP", is_active=True
        )
        Monitor.objects.create(
            user=user, name="M2", url=fake.url(), monitor_type="HTTP", is_active=False
        )

        stats = service.get_dashboard_stats(user)
        assert stats["total"] == 2
        assert stats["active"] == 1
