"""
Webhook Views - API endpoints for managing webhooks.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import WebhookEndpoint, WebhookDelivery
from .serializers import (
    WebhookEndpointSerializer,
    WebhookEndpointCreateSerializer,
    WebhookDeliverySerializer,
    WebhookTestSerializer,
)
from .services import WebhookService


@extend_schema_view(
    list=extend_schema(summary="List Webhook Endpoints", tags=["Webhooks"]),
    create=extend_schema(summary="Create Webhook Endpoint", tags=["Webhooks"]),
    retrieve=extend_schema(summary="Get Webhook Endpoint", tags=["Webhooks"]),
    update=extend_schema(summary="Update Webhook Endpoint", tags=["Webhooks"]),
    partial_update=extend_schema(summary="Partial Update Webhook Endpoint", tags=["Webhooks"]),
    destroy=extend_schema(summary="Delete Webhook Endpoint", tags=["Webhooks"]),
)
class WebhookEndpointViewSet(viewsets.ModelViewSet):
    """ViewSet for managing webhook endpoints."""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return WebhookEndpoint.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return WebhookEndpointCreateSerializer
        return WebhookEndpointSerializer

    def create(self, request, *args, **kwargs):
        """Create webhook endpoint and return full representation."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        endpoint = serializer.save()

        output_serializer = WebhookEndpointSerializer(endpoint, context=self.get_serializer_context())
        headers = self.get_success_headers(output_serializer.data)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @extend_schema(
        summary="Test Webhook Endpoint",
        description="Send a test webhook to verify endpoint configuration.",
        request=WebhookTestSerializer,
        tags=["Webhooks"]
    )
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Send a test webhook."""
        endpoint = self.get_object()
        serializer = WebhookTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        event = serializer.validated_data.get('event', 'application.created')
        result = WebhookService.send_test_webhook(endpoint, event)
        
        if result.get('success'):
            return Response({
                'message': 'Test webhook sent successfully',
                'status_code': result.get('status_code'),
            })
        else:
            return Response({
                'message': 'Test webhook failed',
                'error': result.get('error'),
                'status_code': result.get('status_code'),
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Regenerate Webhook Secret",
        description="Generate a new secret for the webhook endpoint. The old secret will no longer be valid.",
        tags=["Webhooks"]
    )
    @action(detail=True, methods=['post'])
    def regenerate_secret(self, request, pk=None):
        """Regenerate the webhook secret."""
        endpoint = self.get_object()
        new_secret = endpoint.regenerate_secret()
        
        return Response({
            'message': 'Secret regenerated successfully',
            'secret': new_secret,
        })
    
    @extend_schema(
        summary="Get Available Events",
        description="List all available webhook events.",
        tags=["Webhooks"]
    )
    @action(detail=False, methods=['get'])
    def events(self, request):
        """List available webhook events."""
        return Response({
            'events': [
                {'name': name, 'description': desc}
                for name, desc in WebhookEndpoint.EVENT_CHOICES
            ]
        })


@extend_schema_view(
    list=extend_schema(summary="List Webhook Deliveries", tags=["Webhooks"]),
    retrieve=extend_schema(summary="Get Webhook Delivery", tags=["Webhooks"]),
)
class WebhookDeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing webhook delivery logs."""
    
    permission_classes = [IsAuthenticated]
    serializer_class = WebhookDeliverySerializer
    
    def get_queryset(self):
        queryset = WebhookDelivery.objects.filter(
            endpoint__user=self.request.user
        ).select_related('endpoint')
        
        # Filter by endpoint
        endpoint_id = self.request.query_params.get('endpoint')
        if endpoint_id:
            queryset = queryset.filter(endpoint_id=endpoint_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by event
        event = self.request.query_params.get('event')
        if event:
            queryset = queryset.filter(event=event)
        
        return queryset
    
    @extend_schema(
        summary="Retry Webhook Delivery",
        description="Manually retry a failed webhook delivery.",
        tags=["Webhooks"]
    )
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Manually retry a failed delivery."""
        delivery = self.get_object()
        
        if delivery.status == 'success':
            return Response(
                {'error': 'Cannot retry successful delivery'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset for retry
        delivery.status = 'pending'
        delivery.attempt_count = 0
        delivery.error_message = ''
        delivery.save()
        
        # Queue for delivery
        from .tasks import deliver_webhook
        deliver_webhook.delay(str(delivery.id))
        
        return Response({
            'message': 'Webhook queued for retry',
            'delivery_id': str(delivery.id),
        })
