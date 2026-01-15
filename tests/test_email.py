"""
Tests for Email Verification and Password Reset.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestEmailVerification:
    """Test email verification endpoints."""
    
    @patch('apps.users.views.EmailService.send_verification_email')
    def test_register_sends_verification_email(self, mock_send, api_client):
        """Test that registration sends verification email."""
        mock_send.return_value = {'success': True, 'id': 'test-id'}
        
        url = reverse('register')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert mock_send.called
        
        # Check user is not verified
        user = User.objects.get(email='newuser@example.com')
        assert not user.is_email_verified
        assert user.email_verification_token
    
    def test_verify_email_success(self, api_client, db):
        """Test successful email verification."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        token = user.generate_verification_token()
        
        url = reverse('verify_email')
        response = api_client.post(url, {'token': token}, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_email_verified
    
    def test_verify_email_invalid_token(self, api_client, db):
        """Test verification with invalid token."""
        url = reverse('verify_email')
        response = api_client.post(url, {'token': 'invalid-token'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch('apps.users.views.EmailService.send_verification_email')
    def test_resend_verification(self, mock_send, api_client, db):
        """Test resending verification email."""
        mock_send.return_value = {'success': True, 'id': 'test-id'}
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        url = reverse('resend_verification')
        response = api_client.post(url, {'email': user.email}, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert mock_send.called


@pytest.mark.django_db
class TestPasswordReset:
    """Test password reset endpoints."""
    
    @patch('apps.users.views.EmailService.send_password_reset_email')
    def test_password_reset_request(self, mock_send, api_client, db):
        """Test requesting password reset."""
        mock_send.return_value = {'success': True, 'id': 'test-id'}
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        url = reverse('password_reset_request')
        response = api_client.post(url, {'email': user.email}, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert mock_send.called
        
        user.refresh_from_db()
        assert user.password_reset_token
    
    def test_password_reset_request_nonexistent_email(self, api_client):
        """Test reset request doesn't reveal if email exists."""
        url = reverse('password_reset_request')
        response = api_client.post(url, {'email': 'nonexistent@example.com'}, format='json')
        
        # Should still return 200 to not reveal if email exists
        assert response.status_code == status.HTTP_200_OK
    
    @patch('apps.users.views.EmailService.send_password_changed_email')
    def test_password_reset_confirm(self, mock_send, api_client, db):
        """Test confirming password reset."""
        mock_send.return_value = {'success': True, 'id': 'test-id'}
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpass123'
        )
        token = user.generate_password_reset_token()
        
        url = reverse('password_reset_confirm')
        data = {
            'token': token,
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        user.refresh_from_db()
        assert user.check_password('newpass123')
        assert not user.password_reset_token
    
    def test_password_reset_confirm_invalid_token(self, api_client):
        """Test reset confirm with invalid token."""
        url = reverse('password_reset_confirm')
        data = {
            'token': 'invalid-token',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_password_reset_confirm_mismatch(self, api_client, db):
        """Test reset with mismatched passwords."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpass123'
        )
        token = user.generate_password_reset_token()
        
        url = reverse('password_reset_confirm')
        data = {
            'token': token,
            'new_password': 'newpass123',
            'new_password_confirm': 'differentpass'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
