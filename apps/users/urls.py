from django.urls import path

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    ChangePasswordView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProfileView,
    RegisterView,
    ResendVerificationView,
    VerifyEmailView,
    logout_view,
)

urlpatterns = [
    # Authentication
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Email Verification
    path("verify-email/", VerifyEmailView.as_view(), name="verify_email"),
    path("resend-verification/", ResendVerificationView.as_view(), name="resend_verification"),
    # Password Reset
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    # Profile
    path("profile/", ProfileView.as_view(), name="profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
]
