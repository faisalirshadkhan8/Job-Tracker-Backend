"""
Two-Factor Authentication Serializers.
"""

from rest_framework import serializers


class TwoFactorSetupSerializer(serializers.Serializer):
    """Response serializer for 2FA setup."""
    
    secret = serializers.CharField(help_text="TOTP secret (save this securely)")
    qr_code = serializers.CharField(help_text="Base64-encoded QR code image")
    backup_codes = serializers.ListField(
        child=serializers.CharField(),
        help_text="Backup codes for recovery (save these securely)"
    )
    otpauth_url = serializers.CharField(
        required=False,
        help_text="OTPAuth URL for manual entry"
    )


class TwoFactorConfirmSerializer(serializers.Serializer):
    """Serializer for confirming 2FA setup."""
    
    code = serializers.CharField(
        min_length=6,
        max_length=6,
        help_text="6-digit TOTP code from authenticator app"
    )
    
    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Code must contain only digits")
        return value


class TwoFactorVerifySerializer(serializers.Serializer):
    """Serializer for verifying 2FA code."""
    
    code = serializers.CharField(
        min_length=6,
        max_length=10,
        help_text="6-digit TOTP code or 8-character backup code"
    )


class TwoFactorDisableSerializer(serializers.Serializer):
    """Serializer for disabling 2FA."""
    
    code = serializers.CharField(
        min_length=6,
        max_length=10,
        help_text="6-digit TOTP code or backup code"
    )
    password = serializers.CharField(
        write_only=True,
        help_text="Current account password for confirmation"
    )


class TwoFactorStatusSerializer(serializers.Serializer):
    """Serializer for 2FA status."""
    
    enabled = serializers.BooleanField()
    verified = serializers.BooleanField()
    verified_at = serializers.DateTimeField(allow_null=True)
    last_used_at = serializers.DateTimeField(allow_null=True)
    backup_codes_remaining = serializers.IntegerField()


class BackupCodesRegenerateSerializer(serializers.Serializer):
    """Serializer for regenerating backup codes."""
    
    code = serializers.CharField(
        min_length=6,
        max_length=6,
        help_text="6-digit TOTP code for verification"
    )


class BackupCodesResponseSerializer(serializers.Serializer):
    """Response serializer for backup codes."""
    
    backup_codes = serializers.ListField(
        child=serializers.CharField(),
        help_text="New backup codes (save these securely)"
    )
