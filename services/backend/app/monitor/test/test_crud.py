import pytest
from typing import Any
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from faker import Faker
from monitor.models import Monitor, MonitorResult
from monitor.crud import MonitorCRUD, MonitorResultCRUD

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


@pytest.mark.django_db
class TestMonitorCRUD:

    def test_create(self, user: Any) -> None:
        crud = MonitorCRUD()
        monitor = crud.create(
            user=user, name="Test", url="https://test.com", monitor_type="HTTP"
        )
        assert monitor.id is not None
        assert monitor.name == "Test"
        assert monitor.user == user

    def test_get(self, monitor: Monitor, user: Any) -> None:
        crud = MonitorCRUD()
        result = crud.get(id=monitor.id, user=user)
        assert result.id == monitor.id

    def test_list(self, user: Any) -> None:
        crud = MonitorCRUD()
        Monitor.objects.create(
            user=user, name="M1", url=fake.url(), monitor_type="HTTP"
        )
        Monitor.objects.create(
            user=user, name="M2", url=fake.url(), monitor_type="HTTP"
        )

        result = crud.list(user=user)
        assert result.count() == 2

    def test_update(self, monitor: Monitor) -> None:
        crud = MonitorCRUD()
        updated = crud.update(monitor, name="Updated")
        assert updated.name == "Updated"

    def test_delete(self, monitor: Monitor) -> None:
        crud = MonitorCRUD()
        monitor_id = monitor.id
        crud.delete(monitor)
        assert not Monitor.objects.filter(id=monitor_id).exists()

    def test_filter_by_user(self, user: Any) -> None:
        crud = MonitorCRUD()
        Monitor.objects.create(
            user=user, name="M1", url=fake.url(), monitor_type="HTTP", is_active=True
        )
        Monitor.objects.create(
            user=user, name="M2", url=fake.url(), monitor_type="HTTP", is_active=False
        )

        active = crud.filter_by_user(user, is_active=True)
        assert active.count() == 1

    def test_count_by_user(self, user: Any) -> None:
        crud = MonitorCRUD()
        Monitor.objects.create(
            user=user, name="M1", url=fake.url(), monitor_type="HTTP"
        )
        Monitor.objects.create(
            user=user, name="M2", url=fake.url(), monitor_type="HTTP"
        )

        count = crud.count_by_user(user)
        assert count == 2


@pytest.mark.django_db
class TestMonitorResultCRUD:

    def test_filter_by_monitor_and_period(self, monitor: Monitor) -> None:
        crud = MonitorResultCRUD()
        now = timezone.now()
        MonitorResult.objects.create(
            monitor=monitor, status_code=200, response_time_ms=100, is_up=True
        )

        result = crud.filter_by_monitor_and_period(monitor, now - timedelta(hours=1))
        assert result.count() == 1

    def test_get_stats_aggregate(self, monitor: Monitor) -> None:
        crud = MonitorResultCRUD()
        MonitorResult.objects.create(
            monitor=monitor, status_code=200, response_time_ms=100, is_up=True
        )
        MonitorResult.objects.create(
            monitor=monitor, status_code=500, response_time_ms=200, is_up=False
        )

        qs = MonitorResult.objects.filter(monitor=monitor)
        stats = crud.get_stats_aggregate(qs)

        assert stats["total_checks"] == 2
        assert stats["up_count"] == 1
        assert stats["down_count"] == 1

    def test_get_last_check(self, monitor: Monitor) -> None:
        crud = MonitorResultCRUD()
        result1 = MonitorResult.objects.create(
            monitor=monitor, status_code=200, response_time_ms=100, is_up=True
        )

        last = crud.get_last_check(monitor)
        assert last is not None
        assert last.id == result1.id

    def test_get_history(self, monitor: Monitor) -> None:
        crud = MonitorResultCRUD()
        MonitorResult.objects.create(
            monitor=monitor, status_code=200, response_time_ms=100, is_up=True
        )
        MonitorResult.objects.create(
            monitor=monitor, status_code=200, response_time_ms=150, is_up=True
        )

        history = crud.get_history(monitor)
        assert history.count() == 2

    def test_get_history_with_period(self, monitor: Monitor) -> None:
        crud = MonitorResultCRUD()
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

        history = crud.get_history(monitor, period="24h")
        assert history.count() == 1

    def test_get_recent_failures(self, user: Any, monitor: Monitor) -> None:
        crud = MonitorResultCRUD()
        for i in range(3):
            MonitorResult.objects.create(
                monitor=monitor, status_code=500, response_time_ms=100, is_up=False
            )

        failures = crud.get_recent_failures(user, limit=5)
        assert failures.count() == 3
