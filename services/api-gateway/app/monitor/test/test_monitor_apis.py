import pytest
from typing import Any
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from monitor.models import Monitor

User = get_user_model()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user() -> Any:
    return User.objects.create_user(email="user@example.com", password="testpass123")


@pytest.fixture
def other_user() -> Any:
    return User.objects.create_user(email="other@example.com", password="testpass123")


@pytest.fixture
def authenticated_client(api_client: APIClient, user: Any) -> APIClient:
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestMonitorAPI:

    def test_post_valid_data_returns_201(
        self, authenticated_client: APIClient, user: Any
    ) -> None:
        data = {
            "name": "Test Monitor",
            "url": "https://example.com",
            "monitor_type": "HTTP",
            "interval": 60,
        }
        response = authenticated_client.post("/api/v1/monitors/", data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Test Monitor"
        assert response.data["url"] == "https://example.com"
        assert Monitor.objects.filter(user=user).count() == 1

    def test_post_interval_too_low_returns_400(
        self, authenticated_client: APIClient
    ) -> None:
        data = {
            "name": "Test Monitor",
            "url": "https://example.com",
            "monitor_type": "HTTP",
            "interval": 10,
        }
        response = authenticated_client.post("/api/v1/monitors/", data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "interval" in response.data

    def test_get_sees_only_own_monitors(
        self, authenticated_client: APIClient, user: Any, other_user: Any
    ) -> None:
        Monitor.objects.create(
            user=user, name="My Monitor", url="https://mine.com", monitor_type="HTTP"
        )
        Monitor.objects.create(
            user=other_user,
            name="Other Monitor",
            url="https://other.com",
            monitor_type="HTTP",
        )

        response = authenticated_client.get("/api/v1/monitors/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "My Monitor"

    def test_delete_removes_record(
        self, authenticated_client: APIClient, user: Any
    ) -> None:
        monitor = Monitor.objects.create(
            user=user,
            name="Test Monitor",
            url="https://example.com",
            monitor_type="HTTP",
        )

        response = authenticated_client.delete(f"/api/v1/monitors/{monitor.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Monitor.objects.filter(id=monitor.id).count() == 0

    def test_unauthenticated_request_returns_401(self, api_client: APIClient) -> None:
        response = api_client.get("/api/v1/monitors/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cannot_delete_other_users_monitor(
        self, authenticated_client: APIClient, other_user: Any
    ) -> None:
        monitor = Monitor.objects.create(
            user=other_user,
            name="Other Monitor",
            url="https://other.com",
            monitor_type="HTTP",
        )

        response = authenticated_client.delete(f"/api/v1/monitors/{monitor.id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Monitor.objects.filter(id=monitor.id).count() == 1

    def test_cannot_retrieve_other_users_monitor(
        self, authenticated_client: APIClient, other_user: Any
    ) -> None:
        monitor = Monitor.objects.create(
            user=other_user,
            name="Other Monitor",
            url="https://other.com",
            monitor_type="HTTP",
        )

        response = authenticated_client.get(f"/api/v1/monitors/{monitor.id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_update_other_users_monitor(
        self, authenticated_client: APIClient, other_user: Any
    ) -> None:
        monitor = Monitor.objects.create(
            user=other_user,
            name="Other Monitor",
            url="https://other.com",
            monitor_type="HTTP",
        )

        response = authenticated_client.patch(
            f"/api/v1/monitors/{monitor.id}/", {"name": "Hacked"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        monitor.refresh_from_db()
        assert monitor.name == "Other Monitor"

    def test_ssrf_localhost_blocked(self, authenticated_client: APIClient) -> None:
        data = {
            "name": "SSRF",
            "url": "http://localhost:5432",
            "monitor_type": "HTTP",
            "interval": 60,
        }
        response = authenticated_client.post("/api/v1/monitors/", data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_ssrf_aws_metadata_blocked(self, authenticated_client: APIClient) -> None:
        data = {
            "name": "SSRF",
            "url": "http://169.254.169.254/latest/meta-data/",
            "monitor_type": "HTTP",
            "interval": 60,
        }
        response = authenticated_client.post("/api/v1/monitors/", data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_ssrf_private_ip_blocked(self, authenticated_client: APIClient) -> None:
        data = {
            "name": "SSRF",
            "url": "http://192.168.1.1",
            "monitor_type": "HTTP",
            "interval": 60,
        }
        response = authenticated_client.post("/api/v1/monitors/", data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
