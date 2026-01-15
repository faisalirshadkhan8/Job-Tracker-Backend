"""
Webhook Models - Store webhook endpoints and delivery logs.
"""

import secrets
import uuid
from django.db import models
from django.conf import settings


class WebhookEndpoint(models.Model):
    """User-configured webhook endpoint."""
    
    EVENT_CHOICES = [
        ('application.created', 'Application Created'),
        ('application.updated', 'Application Updated'),
        ('application.deleted', 'Application Deleted'),
        ('application.status_changed', 'Application Status Changed'),
        ('interview.created', 'Interview Created'),
        ('interview.updated', 'Interview Updated'),
        ('interview.completed', 'Interview Completed'),
        ('interview.cancelled', 'Interview Cancelled'),
        ('company.created', 'Company Created'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='webhook_endpoints'
    )
    name = models.CharField(max_length=100, help_text="Friendly name for this webhook")
    url = models.URLField(help_text="URL to send webhook payloads to")
    secret = models.CharField(
        max_length=64,
        help_text="Secret for HMAC signature verification"
    )
    events = models.JSONField(
        default=list,
        help_text="List of events to subscribe to"
    )
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Failure tracking
    failure_count = models.PositiveIntegerField(default=0)
    last_failure_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'webhook_endpoints'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.url})"
    
    def save(self, *args, **kwargs):
        if not self.secret:
            self.secret = secrets.token_hex(32)
        super().save(*args, **kwargs)
    
    def regenerate_secret(self):
        """Generate a new secret."""
        self.secret = secrets.token_hex(32)
        self.save(update_fields=['secret', 'updated_at'])
        return self.secret


class WebhookDelivery(models.Model):
    """Log of webhook delivery attempts."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    endpoint = models.ForeignKey(
        WebhookEndpoint,
        on_delete=models.CASCADE,
        related_name='deliveries'
    )
    event = models.CharField(max_length=50)
    payload = models.JSONField()
    
    # Delivery status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    attempt_count = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    
    # Response details
    response_status_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'webhook_deliveries'
        ordering = ['-created_at']
        verbose_name_plural = 'Webhook deliveries'
        indexes = [
            models.Index(fields=['status', 'next_retry_at']),
            models.Index(fields=['endpoint', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.event} -> {self.endpoint.name} ({self.status})"
