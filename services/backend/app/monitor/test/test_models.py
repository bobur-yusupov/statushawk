import pytest
from typing import Any
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from monitor.models import Monitor, MonitorResult

User = get_user_model()


@pytest.fixture
def user() -> Any:
    return User.objects.create_user(email="test@example.com", password="testpass123")


@pytest.mark.django_db
class TestMonitor:
    def test_create_monitor(self, user: Any) -> None:
        monitor = Monitor.objects.create(
            user=user,
            name="Test Monitor",
            url="https://example.com",
            monitor_type=Monitor.MonitorType.HTTP,
        )

        assert monitor.name == "Test Monitor"
        assert monitor.url == "https://example.com"
        assert monitor.monitor_type == Monitor.MonitorType.HTTP
        assert monitor.status == Monitor.StatusType.PAUSED
        assert monitor.interval == 300
        assert monitor.is_active is True

    def test_monitor_str(self, user: Any) -> None:
        monitor = Monitor.objects.create(
            user=user,
            name="Test Monitor",
            url="https://example.com",
            monitor_type=Monitor.MonitorType.HTTP,
        )

        assert str(monitor) == "Test Monitor (https://example.com)"

    def test_monitor_default_values(self, user: Any) -> None:
        monitor = Monitor.objects.create(
            user=user,
            name="Test",
            url="https://example.com",
            monitor_type=Monitor.MonitorType.PING,
        )

        assert monitor.status == Monitor.StatusType.PAUSED
        assert monitor.interval == 300
        assert monitor.is_active is True
        assert monitor.last_checked_at is None

    def test_monitor_interval_validation(self, user: Any) -> None:
        monitor = Monitor(
            user=user,
            name="Test",
            url="https://example.com",
            monitor_type=Monitor.MonitorType.HTTP,
            interval=20,
        )

        with pytest.raises(ValidationError):
            monitor.full_clean()

    def test_monitor_cascade_delete(self, user: Any) -> None:
        Monitor.objects.create(
            user=user,
            name="Test",
            url="https://example.com",
            monitor_type=Monitor.MonitorType.HTTP,
        )

        user.delete()
        assert Monitor.objects.count() == 0

    def test_monitor_types(self, user: Any) -> None:
        for monitor_type in [Monitor.MonitorType.HTTP, Monitor.MonitorType.PING, Monitor.MonitorType.TCP]:
            monitor = Monitor.objects.create(
                user=user,
                name=f"{monitor_type} Monitor",
                url="https://example.com",
                monitor_type=monitor_type,
            )
            assert monitor.monitor_type == monitor_type

    def test_monitor_status_types(self, user: Any) -> None:
        monitor = Monitor.objects.create(
            user=user,
            name="Test",
            url="https://example.com",
            monitor_type=Monitor.MonitorType.HTTP,
        )
        
        for status in [Monitor.StatusType.UP, Monitor.StatusType.DOWN, Monitor.StatusType.PAUSED]:
            monitor.status = status
            monitor.save()
            monitor.refresh_from_db()
            assert monitor.status == status

    def test_monitor_timestamps(self, user: Any) -> None:
        monitor = Monitor.objects.create(
            user=user,
            name="Test",
            url="https://example.com",
            monitor_type=Monitor.MonitorType.HTTP,
        )
        
        assert monitor.created_at is not None
        assert monitor.updated_at is not None
        assert monitor.created_at <= monitor.updated_at


@pytest.mark.django_db
class TestMonitorResult:
    def test_create_monitor_result(self, user: Any) -> None:
        monitor = Monitor.objects.create(
            user=user,
            name="Test",
            url="https://example.com",
            monitor_type=Monitor.MonitorType.HTTP,
        )
        
        result = MonitorResult.objects.create(
            monitor=monitor,
            status_code=200,
            response_time_ms=150,
            is_up=True,
        )
        
        assert result.monitor == monitor
        assert result.status_code == 200
        assert result.response_time_ms == 150
        assert result.is_up is True
        assert result.checked_at is not None

    def test_monitor_result_str(self, user: Any) -> None:
        monitor = Monitor.objects.create(
            user=user,
            name="Test Monitor",
            url="https://example.com",
            monitor_type=Monitor.MonitorType.HTTP,
        )
        
        result = MonitorResult.objects.create(
            monitor=monitor,
            is_up=True,
        )
        
        assert "Test Monitor" in str(result)

    def test_monitor_result_cascade_delete(self, user: Any) -> None:
        monitor = Monitor.objects.create(
            user=user,
            name="Test",
            url="https://example.com",
            monitor_type=Monitor.MonitorType.HTTP,
        )
        
        MonitorResult.objects.create(monitor=monitor, is_up=True)
        MonitorResult.objects.create(monitor=monitor, is_up=False)
        
        assert MonitorResult.objects.filter(monitor=monitor).count() == 2
        
        monitor.delete()
        assert MonitorResult.objects.count() == 0

    def test_monitor_result_nullable_fields(self, user: Any) -> None:
        monitor = Monitor.objects.create(
            user=user,
            name="Test",
            url="https://example.com",
            monitor_type=Monitor.MonitorType.PING,
        )
        
        result = MonitorResult.objects.create(
            monitor=monitor,
            is_up=False,
        )
        
        assert result.status_code is None
        assert result.response_time_ms is None
