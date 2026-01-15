"""
Webhook Signals - Dispatch webhooks on model events.
"""

import logging

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver

from apps.applications.models import Application
from apps.companies.models import Company
from apps.interviews.models import Interview
from .services import WebhookService


logger = logging.getLogger(__name__)


# Store previous values for change detection
_previous_values = {}


def get_application_data(application):
    """Serialize application for webhook payload."""
    return {
        'id': application.id,
        'job_title': application.job_title,
        'company': application.company.name if application.company else None,
        'company_id': application.company_id,
        'status': application.status,
        'applied_date': application.applied_date.isoformat() if application.applied_date else None,
        'job_url': application.job_url,
        'location': application.location,
        'salary_min': application.salary_min,
        'salary_max': application.salary_max,
    }


def get_interview_data(interview):
    """Serialize interview for webhook payload."""
    return {
        'id': interview.id,
        'application_id': interview.application_id,
        'job_title': interview.application.job_title if interview.application else None,
        'company': interview.application.company.name if interview.application and interview.application.company else None,
        'interview_type': interview.interview_type,
        'status': interview.status,
        'scheduled_at': interview.scheduled_at.isoformat() if interview.scheduled_at else None,
        'meeting_location': interview.meeting_location,
        'meeting_link': interview.meeting_link,
        'interviewer_names': interview.interviewer_names,
    }


def get_company_data(company):
    """Serialize company for webhook payload."""
    return {
        'id': company.id,
        'name': company.name,
        'website': company.website,
        'industry': company.industry,
        'location': company.location,
        'notes': company.notes,
    }


# Application Signals
@receiver(pre_save, sender=Application)
def application_pre_save(sender, instance, **kwargs):
    """Store previous status before save."""
    if instance.pk:
        try:
            old = Application.objects.get(pk=instance.pk)
            _previous_values[f'application_{instance.pk}'] = {
                'status': old.status
            }
        except Application.DoesNotExist:
            pass


@receiver(post_save, sender=Application)
def application_post_save(sender, instance, created, **kwargs):
    """Dispatch webhook on application create/update."""
    if created:
        WebhookService.dispatch_event(
            'application.created',
            get_application_data(instance),
            instance.user_id
        )
    else:
        # Check for status change
        prev = _previous_values.pop(f'application_{instance.pk}', {})
        if prev.get('status') != instance.status:
            WebhookService.dispatch_event(
                'application.status_changed',
                {
                    **get_application_data(instance),
                    'previous_status': prev.get('status'),
                    'new_status': instance.status,
                },
                instance.user_id
            )
        else:
            WebhookService.dispatch_event(
                'application.updated',
                get_application_data(instance),
                instance.user_id
            )


@receiver(post_delete, sender=Application)
def application_post_delete(sender, instance, **kwargs):
    """Dispatch webhook on application delete."""
    WebhookService.dispatch_event(
        'application.deleted',
        {
            'id': instance.id,
            'job_title': instance.job_title,
            'company': instance.company.name if instance.company else None,
        },
        instance.user_id
    )


# Interview Signals
@receiver(pre_save, sender=Interview)
def interview_pre_save(sender, instance, **kwargs):
    """Store previous status before save."""
    if instance.pk:
        try:
            old = Interview.objects.get(pk=instance.pk)
            _previous_values[f'interview_{instance.pk}'] = {
                'status': old.status
            }
        except Interview.DoesNotExist:
            pass


@receiver(post_save, sender=Interview)
def interview_post_save(sender, instance, created, **kwargs):
    """Dispatch webhook on interview create/update."""
    user_id = instance.application.user_id if instance.application else None
    if not user_id:
        return
    
    if created:
        WebhookService.dispatch_event(
            'interview.created',
            get_interview_data(instance),
            user_id
        )
    else:
        prev = _previous_values.pop(f'interview_{instance.pk}', {})
        old_status = prev.get('status')
        
        if old_status != instance.status:
            if instance.status == 'completed':
                WebhookService.dispatch_event(
                    'interview.completed',
                    get_interview_data(instance),
                    user_id
                )
            elif instance.status == 'cancelled':
                WebhookService.dispatch_event(
                    'interview.cancelled',
                    get_interview_data(instance),
                    user_id
                )
            else:
                WebhookService.dispatch_event(
                    'interview.updated',
                    get_interview_data(instance),
                    user_id
                )
        else:
            WebhookService.dispatch_event(
                'interview.updated',
                get_interview_data(instance),
                user_id
            )


# Company Signals
@receiver(post_save, sender=Company)
def company_post_save(sender, instance, created, **kwargs):
    """Dispatch webhook on company create."""
    if created:
        WebhookService.dispatch_event(
            'company.created',
            get_company_data(instance),
            instance.user_id
        )
