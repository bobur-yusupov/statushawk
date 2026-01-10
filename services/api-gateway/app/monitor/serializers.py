from rest_framework import serializers
from monitor.models import Monitor


class MonitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Monitor
        fields = ('id', 'name', 'url', 'interval', 'monitor_type', 'status', 'created_at', 'updated_at')
