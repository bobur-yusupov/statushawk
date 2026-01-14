from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MonitorView

app_name = "monitor"
router = DefaultRouter()
router.register("", MonitorView, basename="monitor")

urlpatterns = [
    path("", include(router.urls)),
]
