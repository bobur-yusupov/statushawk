from django.contrib import admin
from .models import NotificationChannel, NotificationLog

@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'user', 'is_active')
    list_filter = ('provider', 'is_active')

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('channel', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at', 'payload_sent')