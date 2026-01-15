"""
Two-Factor Authentication URL Configuration.
"""

from django.urls import path

from .views import (
    BackupCodesRegenerateView,
    TwoFactorConfirmView,
    TwoFactorDisableView,
    TwoFactorSetupView,
    TwoFactorStatusView,
    TwoFactorVerifyView,
)

urlpatterns = [
    path("status/", TwoFactorStatusView.as_view(), name="2fa-status"),
    path("setup/", TwoFactorSetupView.as_view(), name="2fa-setup"),
    path("confirm/", TwoFactorConfirmView.as_view(), name="2fa-confirm"),
    path("verify/", TwoFactorVerifyView.as_view(), name="2fa-verify"),
    path("disable/", TwoFactorDisableView.as_view(), name="2fa-disable"),
    path("backup-codes/regenerate/", BackupCodesRegenerateView.as_view(), name="2fa-backup-codes"),
]
