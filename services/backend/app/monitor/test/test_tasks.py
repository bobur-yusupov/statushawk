import pytest
from typing import Any
from unittest.mock import patch, Mock
from django.contrib.auth import get_user_model
from faker import Faker
from monitor.models import Monitor, MonitorResult
from monitor.tasks import check_monitor_task

User = get_user_model()
fake = Faker()


@pytest.fixture
def user() -> Any:
    return User.objects.create_user(email=fake.email(), password="testpass123")


@pytest.fixture
def monitor(user: Any) -> Monitor:
    return Monitor.objects.create(
        user=user,
        name=fake.company(),
        url="https://example.com",
        monitor_type="HTTP",
        is_active=True,
        interval=60,
    )


@pytest.mark.django_db
class TestCheckMonitorTask:
    """Unit tests for the check_monitor_task"""

    @patch("monitor.tasks.requests.get")
    @patch("monitor.tasks.check_monitor_task.apply_async")
    def test_successful_check(
        self, mock_apply_async: Mock, mock_get: Mock, monitor: Monitor
    ) -> None:
        """Test successful monitor check"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = check_monitor_task(monitor.id)

        assert "Checked https://example.com: 200" in result
        assert MonitorResult.objects.filter(monitor=monitor, is_up=True).exists()
        monitor.refresh_from_db()
        assert monitor.status == "UP"
        assert monitor.last_checked_at is not None
        mock_apply_async.assert_called_once()

    @patch("monitor.tasks.requests.get")
    @patch("monitor.tasks.check_monitor_task.apply_async")
    def test_failed_check(
        self, mock_apply_async: Mock, mock_get: Mock, monitor: Monitor
    ) -> None:
        """Test failed monitor check"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = check_monitor_task(monitor.id)

        assert "Checked https://example.com: 500" in result
        assert MonitorResult.objects.filter(monitor=monitor, is_up=False).exists()
        monitor.refresh_from_db()
        assert monitor.status == "DOWN"

    @patch("monitor.tasks.requests.get")
    @patch("monitor.tasks.check_monitor_task.apply_async")
    def test_timeout_check(
        self, mock_apply_async: Mock, mock_get: Mock, monitor: Monitor
    ) -> None:
        """Test monitor check with timeout"""
        import requests

        mock_get.side_effect = requests.RequestException("Timeout")

        result = check_monitor_task(monitor.id)

        assert "Checked https://example.com: 0" in result
        result_obj = MonitorResult.objects.filter(monitor=monitor).first()
        assert result_obj is not None
        assert result_obj.status_code == 0
        assert result_obj.is_up is False

    @patch("monitor.tasks.check_monitor_task.apply_async")
    def test_inactive_monitor(self, mock_apply_async: Mock, monitor: Monitor) -> None:
        """Test check on inactive monitor"""
        monitor.is_active = False
        monitor.save()

        result = check_monitor_task(monitor.id)

        assert "inactive" in result.lower()
        assert not MonitorResult.objects.filter(monitor=monitor).exists()
        mock_apply_async.assert_not_called()

    @patch("monitor.tasks.check_monitor_task.apply_async")
    def test_nonexistent_monitor(self, mock_apply_async: Mock) -> None:
        """Test check on non-existent monitor"""
        result = check_monitor_task(99999)

        assert "does not exist" in result.lower()
        mock_apply_async.assert_not_called()

    @patch("monitor.tasks.requests.get")
    @patch("monitor.tasks.check_monitor_task.apply_async")
    def test_response_time_recorded(
        self, mock_apply_async: Mock, mock_get: Mock, monitor: Monitor
    ) -> None:
        """Test that response time is recorded"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.150
        mock_get.return_value = mock_response

        check_monitor_task(monitor.id)

        result_obj = MonitorResult.objects.filter(monitor=monitor).first()
        assert result_obj is not None
        assert result_obj.response_time_ms is not None
        assert result_obj.response_time_ms >= 0

    @patch("monitor.tasks.requests.get")
    @patch("monitor.tasks.check_monitor_task.apply_async")
    def test_next_check_scheduled(
        self, mock_apply_async: Mock, mock_get: Mock, monitor: Monitor
    ) -> None:
        """Test that next check is scheduled with correct interval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        check_monitor_task(monitor.id)

        mock_apply_async.assert_called_once()
        call_args = mock_apply_async.call_args
        assert call_args[0][0] == (monitor.id,)
        assert call_args[1]["countdown"] == monitor.interval

    @patch("monitor.tasks.requests.get")
    @patch("monitor.tasks.check_monitor_task.apply_async")
    def test_status_codes_classification(
        self, mock_apply_async: Mock, mock_get: Mock, monitor: Monitor
    ) -> None:
        """Test different status codes are classified correctly"""
        test_cases = [
            (200, True),
            (201, True),
            (299, True),
            (300, False),
            (404, False),
            (500, False),
        ]

        for status_code, expected_is_up in test_cases:
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_get.return_value = mock_response

            check_monitor_task(monitor.id)

            result_obj = MonitorResult.objects.filter(
                monitor=monitor, status_code=status_code
            ).first()
            assert result_obj is not None
            assert result_obj.is_up == expected_is_up

            # Clean up for next iteration
            MonitorResult.objects.filter(monitor=monitor).delete()
