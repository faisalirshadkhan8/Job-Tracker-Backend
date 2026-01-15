"""
Celery Tasks for Notifications.
Handles sending email reminders and notifications.
"""

import logging
from datetime import timedelta

from django.utils import timezone

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def send_interview_reminders():
    """
    Send interview reminder emails.
    Runs every hour via Celery Beat.
    """
    from apps.interviews.models import Interview
    from apps.notifications.models import NotificationLog, NotificationPreference

    now = timezone.now()
    sent_count = 0

    # Get all users with interview reminders enabled
    prefs = NotificationPreference.objects.filter(interview_reminders=True)

    for pref in prefs:
        # Calculate reminder window
        reminder_hours = pref.interview_reminder_hours or 24
        window_start = now
        window_end = now + timedelta(hours=reminder_hours)

        # Find upcoming interviews for this user
        interviews = Interview.objects.filter(
            application__user=pref.user, scheduled_at__range=(window_start, window_end), status="scheduled"
        ).select_related("application", "application__company")

        for interview in interviews:
            # Check if reminder already sent
            already_sent = NotificationLog.objects.filter(
                user=pref.user,
                notification_type="interview_reminder",
                related_object_type="interview",
                related_object_id=interview.id,
                status="sent",
            ).exists()

            if already_sent:
                continue

            # Check quiet hours
            if not _is_within_quiet_hours(pref, now):
                try:
                    # Send reminder email
                    _send_interview_reminder_email(pref.user, interview)

                    # Log success
                    NotificationLog.objects.create(
                        user=pref.user,
                        notification_type="interview_reminder",
                        subject=f"Reminder: Interview at {interview.application.company.name}",
                        status="sent",
                        related_object_type="interview",
                        related_object_id=interview.id,
                        sent_at=timezone.now(),
                    )
                    sent_count += 1
                    logger.info(f"Sent interview reminder to {pref.user.email} for interview {interview.id}")

                except Exception as e:
                    # Log failure
                    NotificationLog.objects.create(
                        user=pref.user,
                        notification_type="interview_reminder",
                        subject=f"Reminder: Interview at {interview.application.company.name}",
                        status="failed",
                        related_object_type="interview",
                        related_object_id=interview.id,
                        error_message=str(e),
                    )
                    logger.error(f"Failed to send interview reminder: {e}")

    logger.info(f"Sent {sent_count} interview reminders")
    return {"reminders_sent": sent_count}


@shared_task
def send_weekly_summary():
    """
    Send weekly job search summary.
    Runs every Monday at 9 AM via Celery Beat.
    """
    from apps.applications.models import Application
    from apps.interviews.models import Interview
    from apps.notifications.models import NotificationLog, NotificationPreference

    now = timezone.now()
    week_ago = now - timedelta(days=7)
    sent_count = 0

    # Get users with weekly summary enabled
    prefs = NotificationPreference.objects.filter(weekly_summary=True)

    for pref in prefs:
        user = pref.user

        # Gather stats for the week
        new_applications = Application.objects.filter(user=user, created_at__gte=week_ago).count()

        status_changes = (
            Application.objects.filter(user=user, updated_at__gte=week_ago)
            .exclude(created_at__gte=week_ago)  # Exclude new ones
            .count()
        )

        interviews_scheduled = Interview.objects.filter(application__user=user, created_at__gte=week_ago).count()

        interviews_completed = Interview.objects.filter(
            application__user=user, status="completed", updated_at__gte=week_ago
        ).count()

        upcoming_interviews = Interview.objects.filter(
            application__user=user, scheduled_at__gte=now, status="scheduled"
        ).count()

        # Skip if no activity
        if new_applications == 0 and status_changes == 0 and interviews_scheduled == 0:
            continue

        try:
            # Send summary email
            _send_weekly_summary_email(
                user, new_applications, status_changes, interviews_scheduled, interviews_completed, upcoming_interviews
            )

            NotificationLog.objects.create(
                user=user,
                notification_type="weekly_summary",
                subject="Your Weekly Job Search Summary",
                status="sent",
                sent_at=timezone.now(),
            )
            sent_count += 1

        except Exception as e:
            NotificationLog.objects.create(
                user=user,
                notification_type="weekly_summary",
                subject="Your Weekly Job Search Summary",
                status="failed",
                error_message=str(e),
            )
            logger.error(f"Failed to send weekly summary to {user.email}: {e}")

    logger.info(f"Sent {sent_count} weekly summaries")
    return {"summaries_sent": sent_count}


@shared_task
def send_application_status_notification(application_id: int, old_status: str, new_status: str):
    """
    Send notification when application status changes.
    Called from Application model signal.
    """
    from apps.applications.models import Application
    from apps.notifications.models import NotificationLog, NotificationPreference

    try:
        application = Application.objects.select_related("user", "company").get(id=application_id)
    except Application.DoesNotExist:
        return

    user = application.user

    # Check if user wants these notifications
    try:
        prefs = NotificationPreference.objects.get(user=user)
        if not prefs.application_updates:
            return
    except NotificationPreference.DoesNotExist:
        # Default to sending if no preferences set
        pass

    try:
        _send_status_change_email(user, application, old_status, new_status)

        NotificationLog.objects.create(
            user=user,
            notification_type="application_status",
            subject=f"Application Update: {application.job_title}",
            status="sent",
            related_object_type="application",
            related_object_id=application.id,
            sent_at=timezone.now(),
        )

    except Exception as e:
        NotificationLog.objects.create(
            user=user,
            notification_type="application_status",
            subject=f"Application Update: {application.job_title}",
            status="failed",
            related_object_type="application",
            related_object_id=application.id,
            error_message=str(e),
        )
        logger.error(f"Failed to send status notification: {e}")


def _is_within_quiet_hours(pref, current_time):
    """Check if current time is within quiet hours."""
    if not pref.quiet_hours_start or not pref.quiet_hours_end:
        return False

    current_time_only = current_time.time()
    start = pref.quiet_hours_start
    end = pref.quiet_hours_end

    # Handle overnight quiet hours (e.g., 22:00 to 08:00)
    if start > end:
        return current_time_only >= start or current_time_only <= end
    else:
        return start <= current_time_only <= end


def _send_interview_reminder_email(user, interview):
    """Send interview reminder email."""
    from services.email_service import EmailService

    context = {
        "user": user,
        "interview": interview,
        "application": interview.application,
        "company": interview.application.company,
        "scheduled_at": interview.scheduled_at,
        "interview_type": interview.get_interview_type_display(),
        "meeting_link": interview.meeting_link,
        "meeting_location": interview.meeting_location,
        "app_name": "Job Application Tracker",
    }

    EmailService.send_email(
        to_email=user.email,
        subject=f"Reminder: {interview.get_interview_type_display()} Interview at {interview.application.company.name}",
        template_name="emails/interview_reminder.html",
        context=context,
    )


def _send_weekly_summary_email(user, new_apps, status_changes, interviews_scheduled, interviews_completed, upcoming):
    """Send weekly summary email."""
    from services.email_service import EmailService

    context = {
        "user": user,
        "new_applications": new_apps,
        "status_changes": status_changes,
        "interviews_scheduled": interviews_scheduled,
        "interviews_completed": interviews_completed,
        "upcoming_interviews": upcoming,
        "app_name": "Job Application Tracker",
    }

    EmailService.send_email(
        to_email=user.email,
        subject="Your Weekly Job Search Summary",
        template_name="emails/weekly_summary.html",
        context=context,
    )


def _send_status_change_email(user, application, old_status, new_status):
    """Send application status change email."""
    from services.email_service import EmailService

    context = {
        "user": user,
        "application": application,
        "company": application.company,
        "old_status": old_status,
        "new_status": new_status,
        "old_status_display": dict(application.STATUS_CHOICES).get(old_status, old_status),
        "new_status_display": dict(application.STATUS_CHOICES).get(new_status, new_status),
        "app_name": "Job Application Tracker",
    }

    EmailService.send_email(
        to_email=user.email,
        subject=f"Application Update: {application.job_title} at {application.company.name}",
        template_name="emails/status_change.html",
        context=context,
    )
