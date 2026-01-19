import ipaddress
from urllib.parse import urlparse
from rest_framework import serializers
from monitor.models import Monitor, MonitorResult


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
        """
        Validates URL format and blocks obvious private/local addresses.
        Note: Deep DNS inspection happens in the worker to avoid API blocking.
        """
        try:
            parsed = urlparse(value)
        except Exception:
            raise serializers.ValidationError("Invalid URL format.")

        if parsed.scheme not in ["http", "https"]:
            raise serializers.ValidationError(
                "Only HTTP and HTTPS schemes are supported"
            )

        hostname = parsed.hostname
        if not hostname:
            raise serializers.ValidationError("URL is missing a hostname")

        if self._is_forbidden_host(hostname):
            raise serializers.ValidationError(
                "Monitoring localhost, private IPs, or metadata services is not allowed"
            )

        return value

    def _is_forbidden_host(self, hostname: str) -> bool:
        """Checks if the hostname is a restricted local or private address."""
        hostname_lower = hostname.lower()

        if hostname_lower in ["localhost", "127.0.0.1", "::1"]:
            return True

        # 2. Block Cloud Metadata IP (AWS/GCP/Azure common magic IP)
        if hostname_lower == "169.254.169.254":
            return True

        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return True

        except ValueError:
            pass

        return False


class MonitorHistorySerializer(serializers.ModelSerializer):
    """Used for graphing response times over time"""

    class Meta:
        model = MonitorResult
        fields = ("id", "status_code", "response_time_ms", "is_up", "created_at")
        read_only_fields = fields


class MonitorStatsSerializer(serializers.Serializer):
    """
    Serializer for aggregated dashboard statistics.
    Does not correspond to a database model directly.
    """

    period = serializers.CharField()
    total_checks = serializers.IntegerField()
    up_count = serializers.IntegerField()
    down_count = serializers.IntegerField()
    uptime_percentage = serializers.FloatField()
    avg_response_time = serializers.FloatField()
    last_check = MonitorHistorySerializer(allow_null=True)
