"""
Tests for Two-Factor Authentication.
"""

import pytest
from unittest.mock import patch, MagicMock

import pyotp
from django.urls import reverse
from rest_framework import status

from apps.twofa.models import TwoFactorDevice, BackupCode
from apps.twofa.services import TwoFactorService


@pytest.mark.django_db
class TestTwoFactorSetup:
    """Tests for 2FA setup."""
    
    def test_get_2fa_status_disabled(self, auth_client, user):
        """Test getting 2FA status when disabled."""
        url = reverse('2fa-status')
        response = auth_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['enabled'] is False
        assert response.data['verified'] is False
    
    def test_setup_2fa(self, auth_client, user):
        """Test setting up 2FA."""
        url = reverse('2fa-setup')
        response = auth_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'secret' in response.data
        assert 'qr_code' in response.data
        assert 'backup_codes' in response.data
        assert len(response.data['backup_codes']) == 10
        
        # Device should be created but not yet enabled
        device = TwoFactorDevice.objects.get(user=user)
        assert device.is_verified is False
        assert device.is_enabled is False
    
    def test_confirm_2fa_valid_code(self, auth_client, user):
        """Test confirming 2FA with valid code."""
        # Setup 2FA first
        device = TwoFactorDevice.objects.create(
            user=user,
            secret=pyotp.random_base32()
        )
        
        # Generate valid code
        totp = pyotp.TOTP(device.secret)
        valid_code = totp.now()
        
        url = reverse('2fa-confirm')
        response = auth_client.post(url, {'code': valid_code})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['enabled'] is True
        
        device.refresh_from_db()
        assert device.is_enabled is True
        assert device.is_verified is True
    
    def test_confirm_2fa_invalid_code(self, auth_client, user):
        """Test confirming 2FA with invalid code."""
        TwoFactorDevice.objects.create(
            user=user,
            secret=pyotp.random_base32()
        )
        
        url = reverse('2fa-confirm')
        response = auth_client.post(url, {'code': '000000'})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_setup_2fa_already_enabled(self, auth_client, user):
        """Test that setup fails if 2FA is already enabled."""
        TwoFactorDevice.objects.create(
            user=user,
            secret=pyotp.random_base32(),
            is_enabled=True,
            is_verified=True
        )
        
        url = reverse('2fa-setup')
        response = auth_client.post(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTwoFactorVerification:
    """Tests for 2FA verification."""
    
    @pytest.fixture
    def enabled_2fa(self, user):
        """Create an enabled 2FA device."""
        device = TwoFactorDevice.objects.create(
            user=user,
            secret=pyotp.random_base32(),
            is_enabled=True,
            is_verified=True
        )
        BackupCode.generate_codes(device)
        return device
    
    def test_verify_totp_valid(self, auth_client, user, enabled_2fa):
        """Test verifying valid TOTP code."""
        totp = pyotp.TOTP(enabled_2fa.secret)
        valid_code = totp.now()
        
        url = reverse('2fa-verify')
        response = auth_client.post(url, {'code': valid_code})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['verified'] is True
        assert response.data['method'] == 'totp'
    
    def test_verify_totp_invalid(self, auth_client, user, enabled_2fa):
        """Test verifying invalid TOTP code."""
        url = reverse('2fa-verify')
        response = auth_client.post(url, {'code': '000000'})
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['verified'] is False
    
    def test_verify_backup_code(self, auth_client, user, enabled_2fa):
        """Test verifying backup code."""
        # Get a backup code
        backup_code = BackupCode.objects.filter(
            device=enabled_2fa,
            is_used=False
        ).first()
        
        # We need to know the actual code - let's generate new ones
        codes = BackupCode.generate_codes(enabled_2fa)
        
        url = reverse('2fa-verify')
        response = auth_client.post(url, {'code': codes[0]})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['verified'] is True
        assert response.data['method'] == 'backup_code'
        
        # Backup code should be marked as used
        used_codes = BackupCode.objects.filter(device=enabled_2fa, is_used=True)
        assert used_codes.count() == 1


@pytest.mark.django_db
class TestTwoFactorDisable:
    """Tests for disabling 2FA."""
    
    @pytest.fixture
    def enabled_2fa(self, user):
        """Create an enabled 2FA device."""
        device = TwoFactorDevice.objects.create(
            user=user,
            secret=pyotp.random_base32(),
            is_enabled=True,
            is_verified=True
        )
        BackupCode.generate_codes(device)
        return device
    
    def test_disable_2fa_valid(self, auth_client, user, enabled_2fa):
        """Test disabling 2FA with valid credentials."""
        totp = pyotp.TOTP(enabled_2fa.secret)
        valid_code = totp.now()
        
        url = reverse('2fa-disable')
        response = auth_client.post(url, {
            'code': valid_code,
            'password': 'testpass123'
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['enabled'] is False
        
        enabled_2fa.refresh_from_db()
        assert enabled_2fa.is_enabled is False
    
    def test_disable_2fa_wrong_password(self, auth_client, user, enabled_2fa):
        """Test disabling 2FA with wrong password."""
        totp = pyotp.TOTP(enabled_2fa.secret)
        valid_code = totp.now()
        
        url = reverse('2fa-disable')
        response = auth_client.post(url, {
            'code': valid_code,
            'password': 'wrongpassword'
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_disable_2fa_wrong_code(self, auth_client, user, enabled_2fa):
        """Test disabling 2FA with wrong code."""
        url = reverse('2fa-disable')
        response = auth_client.post(url, {
            'code': '000000',
            'password': 'testpass123'
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestBackupCodes:
    """Tests for backup codes."""
    
    @pytest.fixture
    def enabled_2fa(self, user):
        """Create an enabled 2FA device."""
        device = TwoFactorDevice.objects.create(
            user=user,
            secret=pyotp.random_base32(),
            is_enabled=True,
            is_verified=True
        )
        BackupCode.generate_codes(device)
        return device
    
    def test_regenerate_backup_codes(self, auth_client, user, enabled_2fa):
        """Test regenerating backup codes."""
        totp = pyotp.TOTP(enabled_2fa.secret)
        valid_code = totp.now()
        
        url = reverse('2fa-backup-codes')
        response = auth_client.post(url, {'code': valid_code})
        
        assert response.status_code == status.HTTP_200_OK
        assert 'backup_codes' in response.data
        assert len(response.data['backup_codes']) == 10
    
    def test_regenerate_backup_codes_invalid_code(self, auth_client, user, enabled_2fa):
        """Test regenerating backup codes with invalid code."""
        url = reverse('2fa-backup-codes')
        response = auth_client.post(url, {'code': '000000'})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_backup_code_can_only_be_used_once(self, user, enabled_2fa):
        """Test that backup codes can only be used once."""
        codes = BackupCode.generate_codes(enabled_2fa)
        
        # First use should succeed
        result1 = BackupCode.verify_code(enabled_2fa, codes[0])
        assert result1 is True
        
        # Second use should fail
        result2 = BackupCode.verify_code(enabled_2fa, codes[0])
        assert result2 is False


@pytest.mark.django_db
class TestTwoFactorService:
    """Tests for 2FA service."""
    
    def test_generate_secret(self):
        """Test secret generation."""
        secret = TwoFactorService.generate_secret()
        
        assert len(secret) == 32
        # Should be valid base32
        assert secret.isalnum()
    
    def test_generate_qr_code(self, user):
        """Test QR code generation."""
        secret = TwoFactorService.generate_secret()
        qr_code = TwoFactorService.generate_qr_code(
            user.email,
            secret
        )
        
        # Should be base64 encoded
        assert len(qr_code) > 0
        import base64
        # Should be valid base64
        decoded = base64.b64decode(qr_code)
        assert decoded.startswith(b'\x89PNG')  # PNG signature
    
    def test_is_2fa_enabled(self, user):
        """Test checking if 2FA is enabled."""
        assert TwoFactorService.is_2fa_enabled(user) is False
        
        TwoFactorDevice.objects.create(
            user=user,
            secret=pyotp.random_base32(),
            is_enabled=True,
            is_verified=True
        )
        
        assert TwoFactorService.is_2fa_enabled(user) is True
    
    def test_get_status(self, user):
        """Test getting 2FA status."""
        status_data = TwoFactorService.get_status(user)
        
        assert status_data['enabled'] is False
        assert status_data['backup_codes_remaining'] == 0
        
        device = TwoFactorDevice.objects.create(
            user=user,
            secret=pyotp.random_base32(),
            is_enabled=True,
            is_verified=True
        )
        BackupCode.generate_codes(device)
        
        status_data = TwoFactorService.get_status(user)
        assert status_data['enabled'] is True
        assert status_data['backup_codes_remaining'] == 10
