from typing import Dict
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

def create_user(email: str = 'test@example.com', password: str = 'testpass123'):
    """Helper function to create a user"""
    return User.objects.create_user(email=email, password=password)

@pytest.mark.django_db
def test_create_user() -> None:

    email: str = 'test@example.com'
    password: str = "SecurePassword!123"
    first_name: str = "John"
    last_name: str = "Doe"

    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )

    # Verify the results
    assert user.email == 'test@example.com'
    assert user.check_password('SecurePassword!123')
    assert user.first_name == "John"
    assert user.last_name == "Doe"

    # Verify user is active by default
    assert user.is_active is True

    # Security Assertion
    assert user.password != password
    assert user.check_password(password) is True

    # Ensure it's not a super/staff by default
    assert user.is_superuser is False
    assert user.is_staff is False

@pytest.mark.django_db
def test_create_user_duplicate_email() -> None:
    email: str = 'test@example.com'
    password: str = "SecurePassword!123"

    create_user(email=email, password=password)

    with pytest.raises(Exception):
        create_user(email=email, password=password)

@pytest.mark.django_db
def test_user_string() -> None:
    user = User.objects.create_user(
        email='test@example.com',
        password='SecurePassword!123',
        first_name='John',
        last_name='Doe',
    )

    assert str(user) == user.email

@pytest.mark.django_db
def test_email_normalization() -> None:
    EMAILS = [
        ('test@EXAMPLE.com', 'test@example.com'),
        ('Admin@Example.Com', 'admin@example.com'),
        ('USER@EXAMPLE.COM', 'user@example.com'),
    ]

    for email, expected in EMAILS:
        user = User.objects.create_user(email=email, password='XXXXXXXXXXXXXX!123')
        assert user.email == expected

@pytest.mark.django_db
def test_create_user_with_short_password() -> None:
    email: str = 'test@example.com'
    password: str = "pw"

    with pytest.raises(Exception):
        User.objects.create_user(email=email, password=password)

@pytest.mark.django_db
def test_create_user_with_no_email() -> None:
    email: str = ''
    password: str = "SecurePassword!123"

    with pytest.raises(Exception):
        User.objects.create_user(email=email, password=password)

@pytest.mark.django_db
def test_create_superuser() -> None:
    email: str = 'test@example.com'
    password: str = "SecurePassword!123"

    user = User.objects.create_superuser(email=email, password=password)

    assert user.is_superuser is True
    assert user.is_staff is True

@pytest.mark.django_db
def test_create_superuser_with_no_email() -> None:
    email: str = ''
    password: str = "SecurePassword!123"

    with pytest.raises(Exception):
        User.objects.create_superuser(email=email, password=password)
