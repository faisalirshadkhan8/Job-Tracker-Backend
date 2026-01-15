"""
Celery Configuration for Job Application Tracker.

This module configures Celery for async task processing.
Redis is used as both the message broker and result backend.
"""

import os

from celery import Celery

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Create Celery app
app = Celery("jobtracker")

# Load config from Django settings
# All Celery-related settings should be prefixed with CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()


# Celery Beat schedule for periodic tasks (optional, for future use)
app.conf.beat_schedule = {
    # Example: Clean up old pending tasks every hour
    # 'cleanup-stale-tasks': {
    #     'task': 'apps.ai.tasks.cleanup_stale_tasks',
    #     'schedule': 3600.0,  # Every hour
    # },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery connection."""
    print(f"Request: {self.request!r}")
