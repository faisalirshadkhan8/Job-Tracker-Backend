"""Two-Factor Authentication app config."""

from django.apps import AppConfig


class TwofaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.twofa"
    verbose_name = "Two-Factor Authentication"
