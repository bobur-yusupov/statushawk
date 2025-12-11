from django.urls import path
from .views import MonitorCheckProxyView

urlpatterns = [
    path("<int:id>/checks/", MonitorCheckProxyView.as_view(), name="monitor-checks")
]
