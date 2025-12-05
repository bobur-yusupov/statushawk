from typing import Dict
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.response import Response
from rest_framework import status

User = get_user_model()

SIGNUP_ENDPOINT: str = reverse("accounts:signup")

@pytest.fixture
def api_client() -> APIClient:
    return APIClient()

@pytest.fixture
def test_user() -> 'AbstractBaseUser':
    return User.objects.create_user(email="test@example.com", password="SecurePassword!123")

@pytest.mark.django_db
def test_signup_success(api_client) -> None:
    payload: Dict[str, str] = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "johndoe@example.com",
        "password": "SecurePassword!123"
    }

    response: Response = api_client.post(path=SIGNUP_ENDPOINT, data=payload, content_type="application/json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["status"] == "ok"

    response_data: Dict[str, str] = response.data["data"]
    
    assert response_data["first_name"] == payload["first_name"]
    assert response_data["last_name"] == payload["last_name"]
    assert response_data["email"] == payload["email"]
    assert response_data["id"] is not None

@pytest.mark.django_db
def test_signup_duplicate_email(api_client, test_user) -> None:
    payload: Dict[str, str] = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "test@example.com",
        "password": "SecurePassword!123"
    }

    response: Response = api_client.post(path=SIGNUP_ENDPOINT, data=payload, content_type="application/json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["status"] == "error"
    assert response.data["data"] is not None

@pytest.mark.django_db
def test_signup_short_password(api_client) -> None:
    payload: Dict[str, str] = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "test@example.com",
        "password": "pw"
    }

    response: Response = api_client.post(path=SIGNUP_ENDPOINT, data=payload, content_type="application/json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["status"] == "error"
    assert response.data["data"] is not None

@pytest.mark.django_db
def test_signup_email_normalization(api_client) -> None:
    payload: Dict[str, str] = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "Test@Example.com",
        "password": "SecurePassword!123"
    }

    response: Response = api_client.post(path=SIGNUP_ENDPOINT, data=payload, content_type="application/json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["status"] == "ok"

    response_data: Dict[str, str] = response.data["data"]

    assert response_data["email"] == payload["email"].lower()

@pytest.mark.django_db
def test_signup_method_not_allowed(api_client, test_user) -> None:
    payload: Dict[str, str] = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "Test@Example.com",
        "password": "SecurePassword!123"
    }

    response: Response = api_client.get(path=SIGNUP_ENDPOINT)

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

@pytest.mark.django_db
def test_signup_unsupported_media_type(test_user) -> None:
    client = APIClient()
    payload: str = "first_name=John&last_name=Doe&email=unsupported@example.com&password=SecurePassword!123"

    response: Response = client.post(
        path=SIGNUP_ENDPOINT,
        data=payload,
        content_type="text/plain",
        REMOTE_ADDR="192.168.1.100"
    )

    assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE

@pytest.mark.django_db
def test_signup_rate_limiting(api_client) -> None:
    payload: Dict[str, str] = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "rate@example.com",
        "password": "SecurePassword!123"
    }

    for _ in range(5):
        api_client.post(
            path=SIGNUP_ENDPOINT,
            data=payload,
            content_type="application/json"
        )

    response = api_client.post(
        path=SIGNUP_ENDPOINT,
        data=payload,
        content_type="application/json"
    )

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
