"""
Tests for Webhook functionality.
"""

import json
from unittest.mock import MagicMock, patch

from django.urls import reverse

from rest_framework import status

import pytest

from apps.webhooks.models import WebhookDelivery, WebhookEndpoint
from apps.webhooks.services import WebhookService


@pytest.fixture
def webhook_endpoint(user):
    """Create a test webhook endpoint."""
    return WebhookEndpoint.objects.create(
        user=user,
        name="Test Webhook",
        url="https://webhook.site/test",
        events=["application.created", "application.status_changed"],
        is_active=True,
    )


@pytest.mark.django_db
class TestWebhookEndpointCRUD:
    """Tests for webhook endpoint CRUD operations."""

    def test_create_webhook_endpoint(self, auth_client, user):
        """Test creating a webhook endpoint."""
        url = reverse("webhook-endpoint-list")
        data = {"name": "My Webhook", "url": "https://example.com/webhook", "events": ["application.created"]}

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "My Webhook"
        assert "secret" in response.data
        assert len(response.data["secret"]) == 64

    def test_list_webhook_endpoints(self, auth_client, user, webhook_endpoint):
        """Test listing webhook endpoints."""
        url = reverse("webhook-endpoint-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Test Webhook"

    def test_get_webhook_endpoint(self, auth_client, user, webhook_endpoint):
        """Test getting a single webhook endpoint."""
        url = reverse("webhook-endpoint-detail", kwargs={"pk": webhook_endpoint.id})
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Webhook"
        assert "delivery_stats" in response.data

    def test_update_webhook_endpoint(self, auth_client, user, webhook_endpoint):
        """Test updating a webhook endpoint."""
        url = reverse("webhook-endpoint-detail", kwargs={"pk": webhook_endpoint.id})
        data = {
            "name": "Updated Webhook",
            "url": "https://example.com/new-webhook",
            "events": ["interview.created"],
            "is_active": False,
        }

        response = auth_client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Webhook"
        assert response.data["is_active"] is False

    def test_delete_webhook_endpoint(self, auth_client, user, webhook_endpoint):
        """Test deleting a webhook endpoint."""
        url = reverse("webhook-endpoint-detail", kwargs={"pk": webhook_endpoint.id})
        response = auth_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not WebhookEndpoint.objects.filter(id=webhook_endpoint.id).exists()

    def test_regenerate_secret(self, auth_client, user, webhook_endpoint):
        """Test regenerating webhook secret."""
        old_secret = webhook_endpoint.secret
        url = reverse("webhook-endpoint-regenerate-secret", kwargs={"pk": webhook_endpoint.id})

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert "secret" in response.data
        assert response.data["secret"] != old_secret

    def test_list_available_events(self, auth_client, user):
        """Test listing available webhook events."""
        url = reverse("webhook-endpoint-events")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "events" in response.data
        events = [e["name"] for e in response.data["events"]]
        assert "application.created" in events
        assert "interview.created" in events


@pytest.mark.django_db
class TestWebhookDeliveries:
    """Tests for webhook delivery logs."""

    def test_list_deliveries(self, auth_client, user, webhook_endpoint):
        """Test listing webhook deliveries."""
        # Create a delivery
        delivery = WebhookDelivery.objects.create(
            endpoint=webhook_endpoint, event="application.created", payload={"test": "data"}, status="success"
        )

        url = reverse("webhook-delivery-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["event"] == "application.created"

    def test_filter_deliveries_by_status(self, auth_client, user, webhook_endpoint):
        """Test filtering deliveries by status."""
        WebhookDelivery.objects.create(
            endpoint=webhook_endpoint, event="application.created", payload={"test": "data"}, status="success"
        )
        WebhookDelivery.objects.create(
            endpoint=webhook_endpoint, event="application.updated", payload={"test": "data"}, status="failed"
        )

        url = reverse("webhook-delivery-list") + "?status=success"
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["status"] == "success"

    def test_retry_failed_delivery(self, auth_client, user, webhook_endpoint):
        """Test retrying a failed delivery."""
        delivery = WebhookDelivery.objects.create(
            endpoint=webhook_endpoint, event="application.created", payload={"test": "data"}, status="failed"
        )

        url = reverse("webhook-delivery-retry", kwargs={"pk": delivery.id})

        with patch("apps.webhooks.tasks.deliver_webhook.delay") as mock_task:
            response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        delivery.refresh_from_db()
        assert delivery.status == "pending"
        mock_task.assert_called_once()


@pytest.mark.django_db
class TestWebhookService:
    """Tests for webhook service."""

    def test_generate_signature(self):
        """Test HMAC signature generation."""
        payload = '{"test": "data"}'
        secret = "test_secret"

        signature = WebhookService.generate_signature(payload, secret)

        assert len(signature) == 64  # SHA256 hex
        # Same input should give same output
        assert signature == WebhookService.generate_signature(payload, secret)

    @patch("apps.webhooks.tasks.deliver_webhook.delay")
    def test_dispatch_event(self, mock_deliver, user, webhook_endpoint):
        """Test dispatching an event to subscribed webhooks."""
        WebhookService.dispatch_event("application.created", {"id": 1, "job_title": "Test"}, user.id)

        # Should create a delivery record
        assert WebhookDelivery.objects.count() == 1
        delivery = WebhookDelivery.objects.first()
        assert delivery.event == "application.created"
        mock_deliver.assert_called_once()

    @patch("apps.webhooks.tasks.deliver_webhook.delay")
    def test_dispatch_event_unsubscribed(self, mock_deliver, user, webhook_endpoint):
        """Test that unsubscribed events are not dispatched."""
        WebhookService.dispatch_event("company.created", {"id": 1}, user.id)  # Not subscribed

        # Should not create a delivery
        assert WebhookDelivery.objects.count() == 0
        mock_deliver.assert_not_called()

    @patch("httpx.Client")
    def test_deliver_success(self, mock_client, webhook_endpoint):
        """Test successful webhook delivery."""
        delivery = WebhookDelivery.objects.create(
            endpoint=webhook_endpoint, event="application.created", payload={"test": "data"}
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        result = WebhookService.deliver(delivery)

        assert result is True
        delivery.refresh_from_db()
        assert delivery.status == "success"
        assert delivery.response_status_code == 200

    @patch("httpx.Client")
    def test_deliver_failure(self, mock_client, webhook_endpoint):
        """Test failed webhook delivery."""
        delivery = WebhookDelivery.objects.create(
            endpoint=webhook_endpoint, event="application.created", payload={"test": "data"}
        )

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        with patch("apps.webhooks.tasks.deliver_webhook.apply_async"):
            result = WebhookService.deliver(delivery)

        assert result is False
        delivery.refresh_from_db()
        assert delivery.status == "retrying"

    @patch("httpx.Client")
    def test_send_test_webhook(self, mock_client, webhook_endpoint):
        """Test sending a test webhook."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        result = WebhookService.send_test_webhook(webhook_endpoint)

        assert result["success"] is True
        assert result["status_code"] == 200
