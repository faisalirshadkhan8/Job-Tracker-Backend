"""
Webhook Serializers.
"""

from rest_framework import serializers

from .models import WebhookEndpoint, WebhookDelivery


class WebhookEndpointSerializer(serializers.ModelSerializer):
    """Serializer for webhook endpoints."""
    
    events = serializers.ListField(
        child=serializers.ChoiceField(
            choices=[e[0] for e in WebhookEndpoint.EVENT_CHOICES]
        )
    )
    secret = serializers.CharField(read_only=True)
    delivery_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = WebhookEndpoint
        fields = [
            'id', 'name', 'url', 'secret', 'events', 'is_active',
            'failure_count', 'last_failure_at', 'last_success_at',
            'created_at', 'updated_at', 'delivery_stats'
        ]
        read_only_fields = ['id', 'secret', 'failure_count', 'last_failure_at', 
                           'last_success_at', 'created_at', 'updated_at']
    
    def get_delivery_stats(self, obj):
        """Get recent delivery statistics."""
        from django.utils import timezone
        from datetime import timedelta
        
        last_24h = timezone.now() - timedelta(hours=24)
        recent_deliveries = obj.deliveries.filter(created_at__gte=last_24h)
        
        return {
            'total_24h': recent_deliveries.count(),
            'successful_24h': recent_deliveries.filter(status='success').count(),
            'failed_24h': recent_deliveries.filter(status='failed').count(),
        }


class WebhookEndpointCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating webhook endpoints."""
    
    events = serializers.ListField(
        child=serializers.ChoiceField(
            choices=[e[0] for e in WebhookEndpoint.EVENT_CHOICES]
        ),
        min_length=1
    )
    
    class Meta:
        model = WebhookEndpoint
        fields = ['name', 'url', 'events', 'is_active']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class WebhookDeliverySerializer(serializers.ModelSerializer):
    """Serializer for webhook delivery logs."""
    
    endpoint_name = serializers.CharField(source='endpoint.name', read_only=True)
    
    class Meta:
        model = WebhookDelivery
        fields = [
            'id', 'endpoint', 'endpoint_name', 'event', 'payload',
            'status', 'attempt_count', 'max_attempts',
            'response_status_code', 'error_message',
            'created_at', 'delivered_at'
        ]
        read_only_fields = fields


class WebhookTestSerializer(serializers.Serializer):
    """Serializer for testing webhook endpoints."""
    
    event = serializers.ChoiceField(
        choices=[e[0] for e in WebhookEndpoint.EVENT_CHOICES],
        default='application.created'
    )
