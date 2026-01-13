from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MonitorCheckProxyView, MonitorView

app_name = "monitor"
router = DefaultRouter()
router.register("", MonitorView, basename="monitor")

urlpatterns = [
    path("", include(router.urls)),
    path("<int:id>/checks/", MonitorCheckProxyView.as_view(), name="monitor-checks"),
]
