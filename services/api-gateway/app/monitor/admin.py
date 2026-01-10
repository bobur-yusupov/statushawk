from django.contrib import admin
from django.utils.html import format_html
from .models import Monitor


@admin.register(Monitor)
class MonitorAdmin(admin.ModelAdmin):
    list_display = ("name", "url_link", "monitor_type", "status_badge", "is_active", "interval", "created_at")
    list_filter = ("monitor_type", "status", "is_active", "created_at")
    search_fields = ("name", "url", "user__email")
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("is_active",)
    list_per_page = 25
    date_hierarchy = "created_at"
    fieldsets = (
        (None, {"fields": ("user", "name", "url")}),
        ("Configuration", {"fields": ("monitor_type", "interval", "status", "is_active")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def url_link(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>', obj.url, obj.url)
    url_link.short_description = "URL"

    def status_badge(self, obj):
        colors = {"UP": "#28a745", "DOWN": "#dc3545", "PAUSED": "#6c757d"}
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; border-radius:3px;">{}</span>',
            colors.get(obj.status, "#6c757d"),
            obj.status
        )
    status_badge.short_description = "Status"
