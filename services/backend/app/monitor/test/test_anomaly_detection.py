import pytest
from typing import Any
from unittest.mock import patch
from django.contrib.auth import get_user_model
from faker import Faker
from monitor.models import Monitor, MonitorResult
from monitor.services import MonitorService

User = get_user_model()
fake = Faker()


@pytest.fixture
def user() -> Any:
    return User.objects.create_user(  # type: ignore[attr-defined]
        email=fake.email(), password="testpass123"
    )


@pytest.fixture
def monitor(user: Any) -> Monitor:
    return Monitor.objects.create(
        user=user, name=fake.company(), url=fake.url(), monitor_type="HTTP"
    )


@pytest.fixture
def service() -> MonitorService:
    return MonitorService()


@pytest.mark.django_db
class TestAnomalyDetection:
    def test_detect_anomaly_insufficient_data(
        self, service: MonitorService, monitor: Monitor
    ) -> None:
        for i in range(5):
            MonitorResult.objects.create(
                monitor=monitor, response_time_ms=100, is_up=True
            )

        service.detect_anomaly(monitor, 500)

    def test_detect_anomaly_no_anomaly(
        self, service: MonitorService, monitor: Monitor
    ) -> None:
        for i in range(20):
            MonitorResult.objects.create(
                monitor=monitor, response_time_ms=100, is_up=True
            )

        with patch.object(service, "_dispatch_anomaly_alert") as mock_alert:
            service.detect_anomaly(monitor, 105)
            mock_alert.assert_not_called()

    @patch("monitor.services.logger")
    def test_detect_anomaly_with_anomaly(
        self, mock_logger: Any, service: MonitorService, monitor: Monitor
    ) -> None:
        for i in range(20):
            MonitorResult.objects.create(
                monitor=monitor, response_time_ms=100 + (i % 3), is_up=True
            )

        with patch.object(service, "_dispatch_anomaly_alert") as mock_alert:
            service.detect_anomaly(monitor, 500)
            mock_alert.assert_called_once()
            assert mock_alert.call_args[0][0] == monitor
            assert mock_alert.call_args[0][1] == 500

    def test_detect_anomaly_zero_variance(
        self, service: MonitorService, monitor: Monitor
    ) -> None:
        for i in range(20):
            MonitorResult.objects.create(
                monitor=monitor, response_time_ms=100, is_up=True
            )

        with patch.object(service, "_dispatch_anomaly_alert") as mock_alert:
            service.detect_anomaly(monitor, 100)
            mock_alert.assert_not_called()

    def test_detect_anomaly_with_none_values(
        self, service: MonitorService, monitor: Monitor
    ) -> None:
        for i in range(15):
            MonitorResult.objects.create(
                monitor=monitor,
                response_time_ms=100 if i % 2 == 0 else None,
                is_up=True,
            )

        service.detect_anomaly(monitor, 500)

    @patch("monitor.services.send_notification_task")
    def test_dispatch_anomaly_alert(
        self, mock_task: Any, service: MonitorService, monitor: Monitor, user: Any
    ) -> None:
        from notifications.models import NotificationChannel

        channel = NotificationChannel.objects.create(
            user=user, name="Test", provider="telegram", config={"chat_id": "123"}
        )

        service._dispatch_anomaly_alert(monitor, 500, 100.0)

        mock_task.apply_async.assert_called_once()
        args = mock_task.apply_async.call_args[1]["args"]
        assert args[0] == channel.id  # type: ignore[attr-defined]
        assert "Performance Warning" in args[1]
        assert "500ms" in args[2]
