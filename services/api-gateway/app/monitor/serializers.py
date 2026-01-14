from rest_framework import serializers
from monitor.models import Monitor, MonitorResult
from urllib.parse import urlparse
import ipaddress


class MonitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Monitor
        fields = (
            "id",
            "name",
            "url",
            "interval",
            "monitor_type",
            "status",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "status", "created_at", "updated_at")

    def validate_url(self, value: str) -> str:
        parsed = urlparse(value)
        hostname = parsed.hostname

        if not hostname:
            raise serializers.ValidationError("Invalid URL")

        if hostname.lower() in ["localhost", "127.0.0.1", "::1"]:
            raise serializers.ValidationError("Monitoring localhost is not allowed")

        if hostname == "169.254.169.254":
            raise serializers.ValidationError(
                "Monitoring metadata endpoints is not allowed"
            )

        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                raise serializers.ValidationError(
                    "Monitoring private IP addresses is not allowed"
                )

        except ValueError:
            pass

        return value


class MonitorHistorySerializer(serializers.ModelSerializer):
    """Used for graphing response times over time"""

    class Meta:
        model = MonitorResult
        fields = ["id", "status_code", "response_time_ms", "is_up", "created_at"]


class MonitorStatsSerializer(serializers.Serializer):
    period = serializers.CharField()
    total_checks = serializers.IntegerField()
    up_count = serializers.IntegerField()
    down_count = serializers.IntegerField()
    uptime_percentage = serializers.FloatField()
    avg_response_time = serializers.FloatField()
    last_check = MonitorHistorySerializer(allow_null=True)
