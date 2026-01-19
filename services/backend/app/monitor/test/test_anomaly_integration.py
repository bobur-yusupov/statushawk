import pytest
from typing import Any
from unittest.mock import patch
from django.contrib.auth import get_user_model
from faker import Faker
from monitor.models import Monitor, MonitorResult
from monitor.services import MonitorService
from notifications.models import NotificationChannel

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
        user=user,
        name=fake.company(),
        url=fake.url(),
        monitor_type="HTTP",
        status=Monitor.StatusType.UP,
    )


@pytest.fixture
def service() -> MonitorService:
    return MonitorService()


@pytest.fixture
def channel(user: Any) -> NotificationChannel:
    return NotificationChannel.objects.create(
        user=user, name="Test", provider="telegram", config={"chat_id": "123"}
    )


@pytest.mark.django_db
class TestAnomalyDetectionIntegration:
    @patch("monitor.services.send_notification_task")
    def test_process_check_result_triggers_anomaly_detection(
        self, mock_task: Any, service: MonitorService, monitor: Monitor, channel: Any
    ) -> None:
        for i in range(20):
            MonitorResult.objects.create(
                monitor=monitor,
                response_time_ms=100 + (i % 3),
                is_up=True,
                status_code=200,
            )

        service.process_check_result(
            monitor_id=monitor.id,  # type: ignore[attr-defined]
            is_up=True,
            response_time=500,
            status_code=200,
        )

        assert mock_task.apply_async.called
        args = mock_task.apply_async.call_args[1]["args"]
        assert "Performance Warning" in args[1]

    def test_process_check_result_no_anomaly_on_status_change(
        self, service: MonitorService, monitor: Monitor
    ) -> None:
        for i in range(20):
            MonitorResult.objects.create(
                monitor=monitor, response_time_ms=100, is_up=True, status_code=200
            )

        with patch.object(service, "detect_anomaly") as mock_detect:
            service.process_check_result(
                monitor_id=monitor.id,  # type: ignore[attr-defined]
                is_up=False,
                response_time=500,
                status_code=500,
            )
            mock_detect.assert_not_called()

    @patch("monitor.services.send_notification_task")
    def test_anomaly_alert_sent_to_all_channels(
        self, mock_task: Any, service: MonitorService, monitor: Monitor, user: Any
    ) -> None:
        NotificationChannel.objects.create(
            user=user, name="Ch1", provider="telegram", config={"chat_id": "1"}
        )
        NotificationChannel.objects.create(
            user=user, name="Ch2", provider="telegram", config={"chat_id": "2"}
        )

        for i in range(20):
            MonitorResult.objects.create(
                monitor=monitor,
                response_time_ms=100 + (i % 3),
                is_up=True,
                status_code=200,
            )

        service.process_check_result(
            monitor_id=monitor.id,  # type: ignore[attr-defined]
            is_up=True,
            response_time=500,
            status_code=200,
        )

        assert mock_task.apply_async.call_count == 2
