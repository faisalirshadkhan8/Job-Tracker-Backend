"""
Tests for Analytics endpoints.
"""

from django.urls import reverse

from rest_framework import status

import pytest


@pytest.mark.django_db
class TestDashboard:
    """Test dashboard endpoint."""

    def test_dashboard_authenticated(self, auth_client, application, interview):
        """Test dashboard returns data."""
        url = reverse("dashboard")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "total_applications" in response.data

    def test_dashboard_unauthenticated(self, api_client):
        """Test dashboard requires auth."""
        url = reverse("dashboard")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestAnalyticsEndpoints:
    """Test various analytics endpoints."""

    def test_response_rate(self, auth_client, application):
        """Test response rate endpoint."""
        url = reverse("response_rate")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_status_funnel(self, auth_client, application):
        """Test status funnel endpoint."""
        url = reverse("status_funnel")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_weekly_activity(self, auth_client, application):
        """Test weekly activity endpoint."""
        url = reverse("weekly_activity")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestHealthChecks:
    """Test health check endpoints."""

    def test_health_check(self, api_client):
        """Test health check endpoint (no auth required)."""
        url = reverse("health_check")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "status" in response.data
        assert "database" in response.data

    def test_liveness_check(self, api_client):
        """Test liveness check endpoint."""
        url = reverse("liveness_check")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["alive"] is True

    def test_readiness_check(self, api_client):
        """Test readiness check endpoint."""
        url = reverse("readiness_check")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
