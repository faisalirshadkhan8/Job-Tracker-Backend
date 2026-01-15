import secrets
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """
    Custom User model for Job Application Tracker.
    Extends Django's AbstractUser with additional fields.
    """

    email = models.EmailField(unique=True)

    # Email verification
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)

    # Password reset
    password_reset_token = models.CharField(max_length=100, blank=True)
    password_reset_sent_at = models.DateTimeField(null=True, blank=True)

    # Profile fields
    phone = models.CharField(max_length=20, blank=True)
    linkedin_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)

    # Job search preferences
    desired_role = models.CharField(max_length=100, blank=True)
    desired_salary_min = models.PositiveIntegerField(null=True, blank=True)
    desired_salary_max = models.PositiveIntegerField(null=True, blank=True)
    preferred_work_type = models.CharField(
        max_length=20,
        choices=[
            ("remote", "Remote"),
            ("hybrid", "Hybrid"),
            ("onsite", "On-site"),
            ("any", "Any"),
        ],
        default="any",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    def generate_verification_token(self):
        """Generate a new email verification token."""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_sent_at = timezone.now()
        self.save(update_fields=["email_verification_token", "email_verification_sent_at"])
        return self.email_verification_token

    def is_verification_token_valid(self, token):
        """Check if verification token is valid (24 hour expiry)."""
        if not self.email_verification_token or self.email_verification_token != token:
            return False
        if not self.email_verification_sent_at:
            return False
        expiry = self.email_verification_sent_at + timedelta(hours=24)
        return timezone.now() < expiry

    def verify_email(self):
        """Mark email as verified."""
        self.is_email_verified = True
        self.email_verification_token = ""
        self.save(update_fields=["is_email_verified", "email_verification_token"])

    def generate_password_reset_token(self):
        """Generate a new password reset token."""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_sent_at = timezone.now()
        self.save(update_fields=["password_reset_token", "password_reset_sent_at"])
        return self.password_reset_token

    def is_password_reset_token_valid(self, token):
        """Check if password reset token is valid (1 hour expiry)."""
        if not self.password_reset_token or self.password_reset_token != token:
            return False
        if not self.password_reset_sent_at:
            return False
        expiry = self.password_reset_sent_at + timedelta(hours=1)
        return timezone.now() < expiry

    def clear_password_reset_token(self):
        """Clear password reset token after use."""
        self.password_reset_token = ""
        self.save(update_fields=["password_reset_token"])
