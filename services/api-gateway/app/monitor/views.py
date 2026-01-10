from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status, mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework.pagination import PageNumberPagination
from django.conf import settings
from django.shortcuts import get_object_or_404
import httpx
from .models import Monitor
from .serializers import MonitorSerializer


class MonitorPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "size"
    max_page_size = 100


class MonitorView(GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = MonitorSerializer
    pagination_class = MonitorPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Monitor.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class MonitorCheckProxyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, monitor_id: int) -> Response:
        # 0. VALIDATE INPUTS
        if not monitor_id:
            return Response(
                {"error": "Monitor ID is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        # 1. AUTHORIZATION (Gateway DB)
        # We verify ownership using the Gateway's local Monitor table.
        # This prevents BOLA (Broken Object Level Authorization).
        # Use get_object_or_404
        monitor = get_object_or_404(Monitor, id=monitor_id, user=request.user)

        # 2. CONSTRUCT INTERNAL REQUEST
        # We target the private K8s service name of the runner.
        runner_url = f"{settings.RUNNER_SERVICE_URL}/api/checks/"

        # 3. PREPARE PARAMS
        # We explicitly set 'target_id' based on the verified monitor.id
        # We pass through safe query params like 'limit'.
        params = {"target_id": monitor.id, "limit": request.GET.get("limit", 50)}

        try:
            response = httpx.get(runner_url, params=params, timeout=3.0)
            return Response(response.json())

        except httpx.RequestError:
            return Response({"error": "Metric"})
