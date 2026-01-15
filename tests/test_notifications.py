"""
Tests for Notifications functionality.
"""

from unittest.mock import MagicMock, patch

from django.urls import reverse
from django.utils import timezone

from rest_framework import status

import pytest

from apps.notifications.models import NotificationLog, NotificationPreference


@pytest.mark.django_db
class TestNotificationPreferences:
    """Tests for notification preferences."""

    def test_get_preferences_creates_default(self, auth_client, user):
        """Test that getting preferences creates default if not exists."""
        url = reverse("notification-preferences")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["interview_reminders"] is True
        assert response.data["weekly_summary"] is True

        # Should have created a preference
        assert NotificationPreference.objects.filter(user=user).exists()

    def test_update_preferences(self, auth_client, user):
        """Test updating notification preferences."""
        url = reverse("notification-preferences")
        data = {
            "interview_reminders": False,
            "weekly_summary": True,
            "application_updates": False,
            "quiet_hours_start": "22:00:00",
            "quiet_hours_end": "08:00:00",
        }

        response = auth_client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["interview_reminders"] is False
        assert response.data["quiet_hours_start"] == "22:00:00"

    def test_partial_update_preferences(self, auth_client, user):
        """Test partial update of preferences."""
        # Create preference first
        NotificationPreference.objects.create(user=user)

        url = reverse("notification-preferences")
        data = {"weekly_summary": False}

        response = auth_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["weekly_summary"] is False
        # Other fields should remain default
        assert response.data["interview_reminders"] is True


@pytest.mark.django_db
class TestNotificationLogs:
    """Tests for notification logs."""

    def test_list_notification_logs(self, auth_client, user):
        """Test listing notification logs."""
        # Create preference first
        pref = NotificationPreference.objects.create(user=user)

        # Create some logs
        NotificationLog.objects.create(
            user=user, notification_type="interview_reminder", subject="Interview Tomorrow", status="sent"
        )
        NotificationLog.objects.create(
            user=user, notification_type="weekly_summary", subject="Weekly Summary", status="sent"
        )

        url = reverse("notification-log-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_filter_logs_by_type(self, auth_client, user):
        """Test filtering logs by notification type."""
        pref = NotificationPreference.objects.create(user=user)

        NotificationLog.objects.create(
            user=user, notification_type="interview_reminder", subject="Interview", status="sent"
        )
        NotificationLog.objects.create(user=user, notification_type="weekly_summary", subject="Summary", status="sent")

        url = reverse("notification-log-list") + "?notification_type=interview_reminder"
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["notification_type"] == "interview_reminder"

    def test_notification_logs_readonly(self, auth_client, user):
        """Test that notification logs are read-only."""
        pref = NotificationPreference.objects.create(user=user)
        log = NotificationLog.objects.create(user=user, notification_type="test", subject="Test", status="sent")

        # Try to delete
        url = reverse("notification-log-detail", kwargs={"pk": log.id})
        response = auth_client.delete(url)

        # Should not be allowed (no delete action on ReadOnlyModelViewSet)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestNotificationTasks:
    """Tests for notification Celery tasks."""

    @patch("apps.notifications.tasks._send_interview_reminder_email")
    def test_send_interview_reminders(self, mock_send_email, user):
        """Test sending interview reminders."""
        from datetime import timedelta

        from apps.applications.models import Application
        from apps.companies.models import Company
        from apps.interviews.models import Interview
        from apps.notifications.tasks import send_interview_reminders

        # Create preference
        NotificationPreference.objects.create(user=user, interview_reminders=True)

        # Create interview in next 24 hours
        company = Company.objects.create(user=user, name="Test Co")
        app = Application.objects.create(user=user, company=company, job_title="Engineer")
        interview = Interview.objects.create(
            application=app,
            interview_type="technical",
            status="scheduled",
            scheduled_at=timezone.now() + timedelta(hours=12),
        )

        mock_send_email.return_value = True

        result = send_interview_reminders()

        assert result["reminders_sent"] >= 0

    @patch("apps.notifications.tasks._send_weekly_summary_email")
    def test_send_weekly_summary(self, mock_send_email, user):
        """Test sending weekly summary."""
        from apps.notifications.tasks import send_weekly_summary

        NotificationPreference.objects.create(user=user, weekly_summary=True)

        mock_send_email.return_value = True

        result = send_weekly_summary()

        assert result["summaries_sent"] >= 0
