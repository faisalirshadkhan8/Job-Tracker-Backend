"""
Webhook Celery Tasks.
"""

import logging

from celery import shared_task

from .models import WebhookDelivery


logger = logging.getLogger(__name__)


@shared_task(
    name='webhooks.deliver_webhook',
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
)
def deliver_webhook(self, delivery_id: str):
    """
    Deliver a webhook.
    
    Args:
        delivery_id: UUID of the WebhookDelivery record
    """
    from .services import WebhookService
    
    try:
        delivery = WebhookDelivery.objects.select_related('endpoint').get(id=delivery_id)
    except WebhookDelivery.DoesNotExist:
        logger.error(f"WebhookDelivery {delivery_id} not found")
        return
    
    if delivery.status == 'success':
        logger.info(f"Webhook {delivery_id} already delivered, skipping")
        return
    
    if not delivery.endpoint.is_active:
        delivery.status = 'failed'
        delivery.error_message = 'Endpoint is disabled'
        delivery.save()
        logger.info(f"Webhook {delivery_id} skipped - endpoint disabled")
        return
    
    WebhookService.deliver(delivery)


@shared_task(name='webhooks.retry_failed_webhooks')
def retry_failed_webhooks():
    """
    Retry webhooks that are scheduled for retry.
    
    This is a fallback in case the scheduled retry task didn't fire.
    Run this every few minutes via celery beat.
    """
    from django.utils import timezone
    
    pending_retries = WebhookDelivery.objects.filter(
        status='retrying',
        next_retry_at__lte=timezone.now()
    )
    
    count = 0
    for delivery in pending_retries[:100]:  # Process up to 100 at a time
        deliver_webhook.delay(str(delivery.id))
        count += 1
    
    if count:
        logger.info(f"Queued {count} webhook retries")
    
    return count


@shared_task(name='webhooks.cleanup_old_deliveries')
def cleanup_old_deliveries(days: int = 30):
    """
    Clean up old webhook delivery records.
    
    Args:
        days: Delete records older than this many days
    """
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff = timezone.now() - timedelta(days=days)
    
    deleted, _ = WebhookDelivery.objects.filter(
        created_at__lt=cutoff,
        status__in=['success', 'failed']
    ).delete()
    
    logger.info(f"Cleaned up {deleted} old webhook deliveries")
    return deleted
