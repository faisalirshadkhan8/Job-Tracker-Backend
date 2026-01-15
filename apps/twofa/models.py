"""
Two-Factor Authentication Models.
"""

import secrets
import uuid

from django.conf import settings
from django.db import models


class TwoFactorDevice(models.Model):
    """TOTP device for 2FA."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="totp_device")

    # TOTP secret (encrypted in production)
    secret = models.CharField(max_length=64)

    # Device status
    is_verified = models.BooleanField(
        default=False, help_text="Whether the device has been verified with a valid TOTP code"
    )
    is_enabled = models.BooleanField(default=False, help_text="Whether 2FA is enabled for this user")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    # Last used tracking
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "twofa_devices"

    def __str__(self):
        status = "enabled" if self.is_enabled else "disabled"
        return f"TOTP device for {self.user.email} ({status})"


class BackupCode(models.Model):
    """Backup codes for 2FA recovery."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(TwoFactorDevice, on_delete=models.CASCADE, related_name="backup_codes")

    # Hashed backup code
    code_hash = models.CharField(max_length=128)

    # Usage tracking
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "twofa_backup_codes"

    def __str__(self):
        status = "used" if self.is_used else "available"
        return f"Backup code ({status})"

    @classmethod
    def generate_codes(cls, device, count=10):
        """
        Generate backup codes for a device.

        Args:
            device: TwoFactorDevice instance
            count: Number of codes to generate

        Returns:
            List of plain text codes (only returned once!)
        """
        import hashlib

        # Delete existing unused codes
        cls.objects.filter(device=device, is_used=False).delete()

        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = secrets.token_hex(4).upper()
            formatted_code = f"{code[:4]}-{code[4:]}"

            # Hash for storage
            code_hash = hashlib.sha256(formatted_code.encode()).hexdigest()

            cls.objects.create(device=device, code_hash=code_hash)
            codes.append(formatted_code)

        return codes

    @classmethod
    def verify_code(cls, device, code):
        """
        Verify and consume a backup code.

        Args:
            device: TwoFactorDevice instance
            code: Plain text backup code

        Returns:
            True if valid, False otherwise
        """
        import hashlib

        from django.utils import timezone

        # Normalize code
        code = code.upper().replace(" ", "").replace("-", "")
        formatted_code = f"{code[:4]}-{code[4:]}" if len(code) == 8 else code
        code_hash = hashlib.sha256(formatted_code.encode()).hexdigest()

        try:
            backup_code = cls.objects.get(device=device, code_hash=code_hash, is_used=False)
            backup_code.is_used = True
            backup_code.used_at = timezone.now()
            backup_code.save()
            return True
        except cls.DoesNotExist:
            return False
