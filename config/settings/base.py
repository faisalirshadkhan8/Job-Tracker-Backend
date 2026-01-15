"""
Base Django settings for Job Application Tracker.
Contains settings common to all environments.
"""

import os
from datetime import timedelta
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "django_celery_beat",
]

LOCAL_APPS = [
    "apps.users",
    "apps.companies",
    "apps.applications",
    "apps.interviews",
    "apps.analytics",
    "apps.ai",
    "apps.notifications",
    "apps.exports",
    "apps.webhooks",
    "apps.twofa",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "middleware.logging.RequestLoggingMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (User uploads)
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Custom User Model
AUTH_USER_MODEL = "users.User"


# Django REST Framework Configuration
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "ai_generate": "20/hour",
    },
}


# JWT Settings
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# Swagger/OpenAPI Settings
SPECTACULAR_SETTINGS = {
    "TITLE": "Job Application Tracker API",
    "DESCRIPTION": "A comprehensive API for tracking job applications, interviews, and analytics.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
        "displayRequestDuration": True,
    },
}


# Email Settings (Resend)
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "onboarding@resend.dev")

# Frontend URL (for email links)
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")


# Celery Configuration
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 180  # 3 minutes max per task
CELERY_TASK_SOFT_TIME_LIMIT = 120  # 2 minutes soft limit
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Enable async AI by default (can be overridden per-request)
AI_ASYNC_ENABLED = os.environ.get("AI_ASYNC_ENABLED", "true").lower() == "true"


# 2FA Settings
TWOFA_ISSUER = "Job Application Tracker"


# Celery Beat Schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "send-interview-reminders": {
        "task": "apps.notifications.tasks.send_interview_reminders",
        "schedule": 3600.0,  # Every hour
    },
    "send-weekly-summary": {
        "task": "apps.notifications.tasks.send_weekly_summary",
        "schedule": crontab(hour=9, minute=0, day_of_week=1),  # Every Monday at 9 AM UTC
    },
    "retry-failed-webhooks": {
        "task": "apps.webhooks.tasks.retry_failed_webhooks",
        "schedule": 300.0,  # Every 5 minutes
    },
    "cleanup-old-webhook-deliveries": {
        "task": "apps.webhooks.tasks.cleanup_old_deliveries",
        "schedule": 86400.0,  # Daily
    },
}
