from typing import Dict, Any
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status

User = get_user_model()

LOGIN_ENDPOINT: str = reverse("accounts:login")
LOGOUT_ENDPOINT: str = reverse("accounts:logout")


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def test_user() -> "AbstractBaseUser":
    return User.objects.create_user(
        email="test@email.com", password="SecurePassword!123"
    )


@pytest.fixture
def auth_api_client(api_client: APIClient, test_user: AbstractBaseUser) -> APIClient:
    api_client.force_authenticate(test_user)
    return api_client


@pytest.mark.django_db
def test_login_success(api_client: APIClient, test_user: AbstractBaseUser) -> None:
    payload: Dict[str, str] = {
        "email": "test@email.com",
        "password": "SecurePassword!123",
    }

    response: Response = api_client.post(
        LOGIN_ENDPOINT, data=payload, content_type="application/json"
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["status"] == "ok"
    assert response.data["timestamp"] is not None

    response_data: Dict[str, Any] = response.data["data"]
    assert response_data["token"] is not None


@pytest.mark.django_db
def test_login_failure_wrong_password(
    api_client: APIClient, test_user: AbstractBaseUser
) -> None:
    payload: Dict[str, str] = {
        "email": "test@email.com",
        "password": "WrongPassword",
    }

    response: Response = api_client.post(
        LOGIN_ENDPOINT, data=payload, content_type="application/json"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["data"] is None
    assert response.data["error"] is not None


@pytest.mark.django_db
def test_login_failure_nonexistent_user(
    api_client: APIClient, test_user: AbstractBaseUser
) -> None:
    payload: Dict[str, str] = {
        "email": "nonexist@email.com",
        "password": "WrongPassword",
    }

    response: Response = api_client.post(
        LOGIN_ENDPOINT, data=payload, content_type="application/json"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_login_missing_fields(
    api_client: APIClient, test_user: AbstractBaseUser
) -> None:
    payload: Dict[str, str] = {
        "password": "WrongPassword",
    }

    response: Response = api_client.post(
        LOGIN_ENDPOINT, data=payload, content_type="application/json"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["data"] is None
    assert response.data["error"] is not None


@pytest.mark.django_db
def test_login_invalid_email_format(
    api_client: APIClient, test_user: AbstractBaseUser
) -> None:
    payload: Dict[str, str] = {
        "email": "user",
        "password": "SecurePassword!123",
    }

    response: Response = api_client.post(
        LOGIN_ENDPOINT, data=payload, content_type="application/json"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_login_empty_strings(test_user: AbstractBaseUser) -> None:
    client = APIClient()
    payload: Dict[str, str] = {
        "email": "",
        "password": "",
    }

    response: Response = client.post(
        LOGIN_ENDPOINT, data=payload, content_type="application/json", REMOTE_ADDR="192.168.1.10"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_login_throttling(api_client: APIClient, test_user: AbstractBaseUser) -> None:
    payload: Dict[str, str] = {
        "email": "user@email.com",
        "password": "WrongPassword",
    }

    for _ in range(5):
        api_client.post(LOGIN_ENDPOINT, data=payload, content_type="application/json")

    response: Response = api_client.post(
        LOGIN_ENDPOINT, data=payload, content_type="application/json"
    )

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.django_db
def test_logout_success(auth_api_client: APIClient) -> None:
    response: Response = auth_api_client.post(LOGOUT_ENDPOINT)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_logout_unauthorized_no_token(api_client: APIClient) -> None:
    response: Response = api_client.post(LOGOUT_ENDPOINT)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_logout_invalid_token(api_client: APIClient) -> None:
    api_client.credentials(HTTP_AUTHORIZATION="Token invalid_token_string")
    response: Response = api_client.post(LOGOUT_ENDPOINT)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_double_logout(test_user: AbstractBaseUser) -> None:
    
    client: APIClient = APIClient()
    token = Token.objects.create(user=test_user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    
    response1: Response = client.post(LOGOUT_ENDPOINT)
    assert response1.status_code == status.HTTP_200_OK

    response2: Response = client.post(LOGOUT_ENDPOINT)
    assert response2.status_code == status.HTTP_401_UNAUTHORIZED
