"""
Notification Serializers.
"""

from rest_framework import serializers
from .models import NotificationPreference, NotificationLog


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for notification preferences."""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'interview_reminders',
            'interview_reminder_hours',
            'application_updates',
            'weekly_summary',
            'quiet_hours_start',
            'quiet_hours_end',
        ]


class NotificationLogSerializer(serializers.ModelSerializer):
    """Serializer for notification history."""
    
    notification_type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    class Meta:
        model = NotificationLog
        fields = [
            'id',
            'notification_type',
            'notification_type_display',
            'subject',
            'status',
            'status_display',
            'sent_at',
            'created_at',
        ]
        read_only_fields = fields
