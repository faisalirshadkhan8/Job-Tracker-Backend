"""
Webhook Service - Handle webhook delivery with retries and signing.
"""

import hashlib
import hmac
import json
import time
import logging
from datetime import timedelta

import httpx
from django.utils import timezone

from .models import WebhookEndpoint, WebhookDelivery


logger = logging.getLogger(__name__)


class WebhookService:
    """Service for dispatching webhooks."""
    
    RETRY_DELAYS = [60, 300, 900]  # 1 min, 5 min, 15 min
    TIMEOUT = 30  # seconds
    
    @classmethod
    def generate_signature(cls, payload: str, secret: str) -> str:
        """
        Generate HMAC-SHA256 signature for payload.
        
        Args:
            payload: JSON payload as string
            secret: Webhook secret
            
        Returns:
            Hex-encoded signature
        """
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    @classmethod
    def dispatch_event(cls, event: str, data: dict, user_id: int):
        """
        Dispatch an event to all subscribed webhooks for a user.
        
        Args:
            event: Event type (e.g., 'application.created')
            data: Event payload data
            user_id: ID of the user who owns the webhooks
        """
        from .tasks import deliver_webhook
        
        endpoints = WebhookEndpoint.objects.filter(
            user_id=user_id,
            is_active=True,
            failure_count__lt=10  # Disable after 10 consecutive failures
        )
        
        for endpoint in endpoints:
            if event in endpoint.events:
                # Create delivery record
                delivery = WebhookDelivery.objects.create(
                    endpoint=endpoint,
                    event=event,
                    payload={
                        'event': event,
                        'timestamp': timezone.now().isoformat(),
                        'data': data
                    }
                )
                
                # Queue for delivery
                deliver_webhook.delay(str(delivery.id))
                
                logger.info(
                    f"Queued webhook delivery {delivery.id} for {event} to {endpoint.name}"
                )
    
    @classmethod
    def deliver(cls, delivery: WebhookDelivery) -> bool:
        """
        Attempt to deliver a webhook.
        
        Args:
            delivery: WebhookDelivery instance
            
        Returns:
            True if successful, False otherwise
        """
        endpoint = delivery.endpoint
        payload_json = json.dumps(delivery.payload, default=str)
        signature = cls.generate_signature(payload_json, endpoint.secret)
        
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Event': delivery.event,
            'X-Webhook-Signature': f'sha256={signature}',
            'X-Webhook-Timestamp': str(int(time.time())),
            'X-Webhook-Delivery-ID': str(delivery.id),
            'User-Agent': 'JobTracker-Webhook/1.0',
        }
        
        delivery.attempt_count += 1
        
        try:
            with httpx.Client(timeout=cls.TIMEOUT) as client:
                response = client.post(
                    endpoint.url,
                    content=payload_json,
                    headers=headers
                )
            
            delivery.response_status_code = response.status_code
            delivery.response_body = response.text[:1000]  # Limit stored response
            
            if 200 <= response.status_code < 300:
                # Success
                delivery.status = 'success'
                delivery.delivered_at = timezone.now()
                delivery.save()
                
                # Update endpoint stats
                endpoint.failure_count = 0
                endpoint.last_success_at = timezone.now()
                endpoint.save(update_fields=['failure_count', 'last_success_at'])
                
                logger.info(f"Webhook {delivery.id} delivered successfully")
                return True
            else:
                # Non-2xx response
                delivery.error_message = f"HTTP {response.status_code}: {response.text[:200]}"
                cls._handle_failure(delivery, endpoint)
                return False
                
        except httpx.TimeoutException as e:
            delivery.error_message = f"Timeout: {str(e)}"
            cls._handle_failure(delivery, endpoint)
            return False
            
        except httpx.RequestError as e:
            delivery.error_message = f"Request error: {str(e)}"
            cls._handle_failure(delivery, endpoint)
            return False
            
        except Exception as e:
            delivery.error_message = f"Unexpected error: {str(e)}"
            cls._handle_failure(delivery, endpoint)
            logger.exception(f"Webhook delivery {delivery.id} failed unexpectedly")
            return False
    
    @classmethod
    def _handle_failure(cls, delivery: WebhookDelivery, endpoint: WebhookEndpoint):
        """Handle delivery failure with retry logic."""
        if delivery.attempt_count < delivery.max_attempts:
            # Schedule retry
            retry_index = min(delivery.attempt_count - 1, len(cls.RETRY_DELAYS) - 1)
            retry_delay = cls.RETRY_DELAYS[retry_index]
            
            delivery.status = 'retrying'
            delivery.next_retry_at = timezone.now() + timedelta(seconds=retry_delay)
            delivery.save()
            
            # Queue retry
            from .tasks import deliver_webhook
            deliver_webhook.apply_async(
                args=[str(delivery.id)],
                countdown=retry_delay
            )
            
            logger.warning(
                f"Webhook {delivery.id} failed, retry {delivery.attempt_count}/{delivery.max_attempts} "
                f"scheduled in {retry_delay}s"
            )
        else:
            # Max retries exceeded
            delivery.status = 'failed'
            delivery.save()
            
            # Update endpoint failure count
            endpoint.failure_count += 1
            endpoint.last_failure_at = timezone.now()
            endpoint.save(update_fields=['failure_count', 'last_failure_at'])
            
            logger.error(
                f"Webhook {delivery.id} permanently failed after {delivery.attempt_count} attempts"
            )
    
    @classmethod
    def send_test_webhook(cls, endpoint: WebhookEndpoint, event: str = 'test') -> dict:
        """
        Send a test webhook to verify endpoint configuration.
        
        Args:
            endpoint: WebhookEndpoint to test
            event: Event type to simulate
            
        Returns:
            dict with success status and details
        """
        test_payload = {
            'event': f'{event}.test',
            'timestamp': timezone.now().isoformat(),
            'data': {
                'message': 'This is a test webhook from Job Application Tracker',
                'endpoint_id': str(endpoint.id),
                'endpoint_name': endpoint.name,
            }
        }
        
        payload_json = json.dumps(test_payload, default=str)
        signature = cls.generate_signature(payload_json, endpoint.secret)
        
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Event': f'{event}.test',
            'X-Webhook-Signature': f'sha256={signature}',
            'X-Webhook-Timestamp': str(int(time.time())),
            'X-Webhook-Delivery-ID': 'test',
            'User-Agent': 'JobTracker-Webhook/1.0',
        }
        
        try:
            with httpx.Client(timeout=10) as client:
                response = client.post(
                    endpoint.url,
                    content=payload_json,
                    headers=headers
                )
            
            return {
                'success': 200 <= response.status_code < 300,
                'status_code': response.status_code,
                'response': response.text[:500],
            }
            
        except httpx.TimeoutException:
            return {
                'success': False,
                'error': 'Request timed out',
            }
            
        except httpx.RequestError as e:
            return {
                'success': False,
                'error': str(e),
            }
