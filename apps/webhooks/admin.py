"""
Webhook Admin Configuration.
"""

from django.contrib import admin

from .models import WebhookDelivery, WebhookEndpoint


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    """Admin for webhook endpoints."""

    list_display = ["name", "user", "url", "is_active", "failure_count", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "url", "user__email"]
    readonly_fields = [
        "id",
        "secret",
        "failure_count",
        "last_failure_at",
        "last_success_at",
        "created_at",
        "updated_at",
    ]

    fieldsets = [
        (None, {"fields": ["id", "user", "name", "url", "secret", "events", "is_active"]}),
        ("Statistics", {"fields": ["failure_count", "last_failure_at", "last_success_at"]}),
        ("Timestamps", {"fields": ["created_at", "updated_at"]}),
    ]


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    """Admin for webhook deliveries."""

    list_display = ["id", "endpoint", "event", "status", "attempt_count", "created_at"]
    list_filter = ["status", "event", "created_at"]
    search_fields = ["endpoint__name", "event"]
    readonly_fields = [
        "id",
        "endpoint",
        "event",
        "payload",
        "status",
        "attempt_count",
        "response_status_code",
        "response_body",
        "error_message",
        "created_at",
        "delivered_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
