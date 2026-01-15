from django.contrib import admin
from .models import NotificationPreference, NotificationLog


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'interview_reminders', 'application_updates', 'weekly_summary']
    search_fields = ['user__email']


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'subject', 'status', 'sent_at', 'created_at']
    list_filter = ['notification_type', 'status']
    search_fields = ['user__email', 'subject']
    readonly_fields = ['created_at', 'sent_at']
