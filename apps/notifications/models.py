"""
Notification Models - Store notification preferences and history.
"""

from django.db import models
from django.conf import settings


class NotificationPreference(models.Model):
    """User notification preferences."""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Email notification toggles
    interview_reminders = models.BooleanField(default=True)
    interview_reminder_hours = models.PositiveSmallIntegerField(default=24)  # Hours before
    
    application_updates = models.BooleanField(default=True)
    weekly_summary = models.BooleanField(default=True)
    
    # Quiet hours (don't send during these hours)
    quiet_hours_start = models.TimeField(null=True, blank=True)  # e.g., 22:00
    quiet_hours_end = models.TimeField(null=True, blank=True)    # e.g., 08:00
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.email}"


class NotificationLog(models.Model):
    """Log of sent notifications for tracking."""
    
    NOTIFICATION_TYPES = [
        ('interview_reminder', 'Interview Reminder'),
        ('application_status', 'Application Status Change'),
        ('weekly_summary', 'Weekly Summary'),
        ('custom', 'Custom Notification'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_logs'
    )
    
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Reference to related object
    related_object_type = models.CharField(max_length=50, blank=True)  # e.g., 'interview'
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'notification_type']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} - {self.user.email} - {self.status}"
