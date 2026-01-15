"""
Two-Factor Authentication Service.
"""

import base64
import io
import logging
from typing import Optional, Tuple

from django.conf import settings
from django.utils import timezone

import pyotp
import qrcode

from .models import BackupCode, TwoFactorDevice

logger = logging.getLogger(__name__)


class TwoFactorService:
    """Service for handling 2FA operations."""

    # TOTP settings
    TOTP_DIGITS = 6
    TOTP_INTERVAL = 30  # seconds
    TOTP_VALID_WINDOW = 1  # Allow 1 interval before/after

    @classmethod
    def generate_secret(cls) -> str:
        """Generate a new TOTP secret."""
        return pyotp.random_base32()

    @classmethod
    def setup_2fa(cls, user) -> Tuple[str, str, list]:
        """
        Set up 2FA for a user.

        Args:
            user: User instance

        Returns:
            Tuple of (secret, qr_code_base64, backup_codes)
        """
        # Check if device already exists
        device, created = TwoFactorDevice.objects.get_or_create(user=user, defaults={"secret": cls.generate_secret()})

        if not created and device.is_enabled:
            raise ValueError("2FA is already enabled for this user")

        # Generate new secret if re-setting up
        if not created:
            device.secret = cls.generate_secret()
            device.is_verified = False
            device.is_enabled = False
            device.save()

        # Generate QR code
        qr_code = cls.generate_qr_code(user.email, device.secret)

        # Generate backup codes
        backup_codes = BackupCode.generate_codes(device)

        logger.info(f"2FA setup initiated for user {user.id}")

        return device.secret, qr_code, backup_codes

    @classmethod
    def generate_qr_code(cls, email: str, secret: str) -> str:
        """
        Generate QR code for TOTP setup.

        Args:
            email: User's email for display
            secret: TOTP secret

        Returns:
            Base64-encoded QR code image
        """
        issuer = getattr(settings, "TWOFA_ISSUER", "Job Application Tracker")

        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=email, issuer_name=issuer)

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode()

    @classmethod
    def verify_totp(cls, user, code: str) -> bool:
        """
        Verify a TOTP code.

        Args:
            user: User instance
            code: 6-digit TOTP code

        Returns:
            True if valid, False otherwise
        """
        try:
            device = TwoFactorDevice.objects.get(user=user)
        except TwoFactorDevice.DoesNotExist:
            return False

        totp = pyotp.TOTP(device.secret)

        if totp.verify(code, valid_window=cls.TOTP_VALID_WINDOW):
            device.last_used_at = timezone.now()
            device.save(update_fields=["last_used_at"])
            return True

        return False

    @classmethod
    def confirm_setup(cls, user, code: str) -> bool:
        """
        Confirm 2FA setup with initial code verification.

        Args:
            user: User instance
            code: 6-digit TOTP code

        Returns:
            True if setup confirmed, False otherwise
        """
        try:
            device = TwoFactorDevice.objects.get(user=user)
        except TwoFactorDevice.DoesNotExist:
            return False

        if device.is_enabled:
            return False  # Already enabled

        if cls.verify_totp(user, code):
            device.is_verified = True
            device.is_enabled = True
            device.verified_at = timezone.now()
            device.save()

            logger.info(f"2FA enabled for user {user.id}")
            return True

        return False

    @classmethod
    def disable_2fa(cls, user, code: str) -> bool:
        """
        Disable 2FA for a user.

        Args:
            user: User instance
            code: 6-digit TOTP code or backup code

        Returns:
            True if disabled, False otherwise
        """
        try:
            device = TwoFactorDevice.objects.get(user=user)
        except TwoFactorDevice.DoesNotExist:
            return False

        if not device.is_enabled:
            return False

        # Verify with TOTP or backup code
        if cls.verify_totp(user, code) or BackupCode.verify_code(device, code):
            device.is_enabled = False
            device.is_verified = False
            device.save()

            # Delete backup codes
            BackupCode.objects.filter(device=device).delete()

            logger.info(f"2FA disabled for user {user.id}")
            return True

        return False

    @classmethod
    def is_2fa_enabled(cls, user) -> bool:
        """Check if 2FA is enabled for a user."""
        try:
            device = TwoFactorDevice.objects.get(user=user)
            return device.is_enabled
        except TwoFactorDevice.DoesNotExist:
            return False

    @classmethod
    def get_status(cls, user) -> dict:
        """Get 2FA status for a user."""
        try:
            device = TwoFactorDevice.objects.get(user=user)
            backup_codes_remaining = BackupCode.objects.filter(device=device, is_used=False).count()

            return {
                "enabled": device.is_enabled,
                "verified": device.is_verified,
                "verified_at": device.verified_at,
                "last_used_at": device.last_used_at,
                "backup_codes_remaining": backup_codes_remaining,
            }
        except TwoFactorDevice.DoesNotExist:
            return {
                "enabled": False,
                "verified": False,
                "verified_at": None,
                "last_used_at": None,
                "backup_codes_remaining": 0,
            }

    @classmethod
    def regenerate_backup_codes(cls, user, code: str) -> Optional[list]:
        """
        Regenerate backup codes.

        Args:
            user: User instance
            code: TOTP code for verification

        Returns:
            List of new backup codes or None if verification failed
        """
        try:
            device = TwoFactorDevice.objects.get(user=user)
        except TwoFactorDevice.DoesNotExist:
            return None

        if not device.is_enabled:
            return None

        if not cls.verify_totp(user, code):
            return None

        new_codes = BackupCode.generate_codes(device)
        logger.info(f"Backup codes regenerated for user {user.id}")

        return new_codes

    @classmethod
    def verify_backup_code(cls, user, code: str) -> bool:
        """
        Verify a backup code.

        Args:
            user: User instance
            code: Backup code

        Returns:
            True if valid, False otherwise
        """
        try:
            device = TwoFactorDevice.objects.get(user=user)
        except TwoFactorDevice.DoesNotExist:
            return False

        return BackupCode.verify_code(device, code)
