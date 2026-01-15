from typing import List, Union
from django.contrib import admin
from django.conf import settings
from django.urls import path, include, URLPattern, URLResolver

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from common.views import HealthCheckView

urlpatterns: List[Union[URLPattern, URLResolver]] = [
    path("admin/", admin.site.urls),
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("api/v1/accounts/", include("accounts.urls")),
    path("api/v1/monitors/", include("monitor.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        path("api/schema", SpectacularAPIView.as_view(), name="api-schema"),
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(url_name="api-schema"),
            name="api-docs",
        ),
    ]
