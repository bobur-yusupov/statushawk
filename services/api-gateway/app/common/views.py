from django.http import JsonResponse, HttpRequest
from django.views import View


class HealthCheckView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        return JsonResponse({"status": "ok"})
