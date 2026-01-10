import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from monitor.models import Monitor

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(email="test@example.com", password="testpass123")


@pytest.mark.django_db
def test_create_monitor(user):
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
    assert monitor.interval == 60
    assert monitor.is_active is True


@pytest.mark.django_db
def test_monitor_str(user):
    monitor = Monitor.objects.create(
        user=user,
        name="Test Monitor",
        url="https://example.com",
        monitor_type=Monitor.MonitorType.HTTP,
    )
    
    assert str(monitor) == "Test Monitor (https://example.com)"


@pytest.mark.django_db
def test_monitor_default_values(user):
    monitor = Monitor.objects.create(
        user=user,
        name="Test",
        url="https://example.com",
        monitor_type=Monitor.MonitorType.PING,
    )
    
    assert monitor.status == Monitor.StatusType.PAUSED
    assert monitor.interval == 60
    assert monitor.is_active is True


@pytest.mark.django_db
def test_monitor_interval_validation(user):
    monitor = Monitor(
        user=user,
        name="Test",
        url="https://example.com",
        monitor_type=Monitor.MonitorType.HTTP,
        interval=20,
    )
    
    with pytest.raises(ValidationError):
        monitor.full_clean()


@pytest.mark.django_db
def test_monitor_cascade_delete(user):
    Monitor.objects.create(
        user=user,
        name="Test",
        url="https://example.com",
        monitor_type=Monitor.MonitorType.HTTP,
    )
    
    user.delete()
    assert Monitor.objects.count() == 0
