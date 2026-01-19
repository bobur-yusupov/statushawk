import pytest
from typing import Any
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from faker import Faker
from monitor.models import Monitor, MonitorResult

User = get_user_model()
fake = Faker()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user() -> Any:
    return User.objects.create_user(email=fake.email(), password="testpass123")


@pytest.fixture
def authenticated_client(api_client: APIClient, user: Any) -> APIClient:
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestMonitorIntegration:
    """Integration tests for the full stack: View -> Service -> CRUD -> DB"""

    def test_create_monitor_full_stack(
        self, authenticated_client: APIClient, user: Any
    ) -> None:
        """Test creating a monitor through the API"""
        data = {
            "name": "Integration Test",
            "url": "https://example.com",
            "monitor_type": "HTTP",
            "interval": 60,
        }
        response = authenticated_client.post("/api/v1/monitors/", data)

        assert response.status_code == status.HTTP_201_CREATED
        assert Monitor.objects.filter(user=user, name="Integration Test").exists()

    def test_list_monitors_full_stack(
        self, authenticated_client: APIClient, user: Any
    ) -> None:
        """Test listing monitors through the API"""
        Monitor.objects.create(
            user=user, name="M1", url=fake.url(), monitor_type="HTTP"
        )
        Monitor.objects.create(
            user=user, name="M2", url=fake.url(), monitor_type="HTTP"
        )

        response = authenticated_client.get("/api/v1/monitors/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_update_monitor_full_stack(
        self, authenticated_client: APIClient, user: Any
    ) -> None:
        """Test updating a monitor through the API"""
        monitor = Monitor.objects.create(
            user=user, name="Old", url=fake.url(), monitor_type="HTTP"
        )

        response = authenticated_client.patch(
            f"/api/v1/monitors/{monitor.id}/", {"name": "New"}
        )

        assert response.status_code == status.HTTP_200_OK
        monitor.refresh_from_db()
        assert monitor.name == "New"

    def test_delete_monitor_full_stack(
        self, authenticated_client: APIClient, user: Any
    ) -> None:
        """Test deleting a monitor through the API"""
        monitor = Monitor.objects.create(
            user=user, name="Delete Me", url=fake.url(), monitor_type="HTTP"
        )
        monitor_id = monitor.id

        response = authenticated_client.delete(f"/api/v1/monitors/{monitor_id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Monitor.objects.filter(id=monitor_id).exists()

    def test_stats_full_stack(self, authenticated_client: APIClient, user: Any) -> None:
        """Test getting stats through the API"""
        monitor = Monitor.objects.create(
            user=user, name="Stats Test", url=fake.url(), monitor_type="HTTP"
        )

        for i in range(5):
            MonitorResult.objects.create(
                monitor=monitor, status_code=200, response_time_ms=100, is_up=True
            )

        response = authenticated_client.get(
            f"/api/v1/monitors/{monitor.id}/stats/?period=24h"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_checks"] == 5
        assert response.data["uptime_percentage"] == 100.0

    def test_history_full_stack(
        self, authenticated_client: APIClient, user: Any
    ) -> None:
        """Test getting history through the API"""
        monitor = Monitor.objects.create(
            user=user, name="History Test", url=fake.url(), monitor_type="HTTP"
        )

        for i in range(3):
            MonitorResult.objects.create(
                monitor=monitor, status_code=200, response_time_ms=100, is_up=True
            )

        response = authenticated_client.get(f"/api/v1/monitors/{monitor.id}/history/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_dashboard_stats_full_stack(
        self, authenticated_client: APIClient, user: Any
    ) -> None:
        """Test getting dashboard stats through the API"""
        m1 = Monitor.objects.create(
            user=user,
            name="M1",
            url=fake.url(),
            monitor_type="HTTP",
            is_active=True,
            status=Monitor.StatusType.UP,
        )
        m2 = Monitor.objects.create(
            user=user,
            name="M2",
            url=fake.url(),
            monitor_type="HTTP",
            is_active=True,
            status=Monitor.StatusType.DOWN,
        )

        MonitorResult.objects.create(
            monitor=m1, status_code=200, response_time_ms=100, is_up=True
        )
        MonitorResult.objects.create(
            monitor=m2, status_code=500, response_time_ms=200, is_up=False
        )

        response = authenticated_client.get("/api/v1/monitors/dashboard_stats/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total"] == 2
        assert response.data["up"] == 1
        assert response.data["down"] == 1

    def test_user_isolation_full_stack(
        self, authenticated_client: APIClient, user: Any
    ) -> None:
        """Test that users can only see their own monitors"""
        other_user = User.objects.create_user(
            email=fake.email(), password="testpass123"
        )

        Monitor.objects.create(
            user=user, name="My Monitor", url=fake.url(), monitor_type="HTTP"
        )
        Monitor.objects.create(
            user=other_user, name="Other Monitor", url=fake.url(), monitor_type="HTTP"
        )

        response = authenticated_client.get("/api/v1/monitors/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "My Monitor"

    def test_pagination_full_stack(
        self, authenticated_client: APIClient, user: Any
    ) -> None:
        """Test pagination through the API"""
        for i in range(15):
            Monitor.objects.create(
                user=user, name=f"M{i}", url=fake.url(), monitor_type="HTTP"
            )

        response = authenticated_client.get("/api/v1/monitors/?size=5")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 5
        assert response.data["count"] == 15

    def test_stats_with_period_filter_full_stack(
        self, authenticated_client: APIClient, user: Any
    ) -> None:
        """Test stats with different period filters"""
        monitor = Monitor.objects.create(
            user=user, name="Period Test", url=fake.url(), monitor_type="HTTP"
        )
        now = timezone.now()

        # Create results in different time periods
        result1 = MonitorResult.objects.create(
            monitor=monitor, status_code=200, response_time_ms=100, is_up=True
        )
        result1.created_at = now - timedelta(hours=12)
        result1.save()

        result2 = MonitorResult.objects.create(
            monitor=monitor, status_code=200, response_time_ms=100, is_up=True
        )
        result2.created_at = now - timedelta(days=5)
        result2.save()

        # Test 24h period
        response = authenticated_client.get(
            f"/api/v1/monitors/{monitor.id}/stats/?period=24h"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_checks"] == 1

        # Test 7d period
        response = authenticated_client.get(
            f"/api/v1/monitors/{monitor.id}/stats/?period=7d"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_checks"] == 2
