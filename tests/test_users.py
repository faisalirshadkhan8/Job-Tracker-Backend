"""
Tests for User Authentication and Profile.
"""

from django.urls import reverse

from rest_framework import status

import pytest


@pytest.mark.django_db
class TestUserRegistration:
    """Test user registration endpoint."""

    def test_register_success(self, api_client):
        """Test successful user registration."""
        url = reverse("register")
        data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "securepass123",
            "password_confirm": "securepass123",
            "first_name": "New",
            "last_name": "User",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "tokens" in response.data
        assert "access" in response.data["tokens"]
        assert "refresh" in response.data["tokens"]

    def test_register_password_mismatch(self, api_client):
        """Test registration with mismatched passwords."""
        url = reverse("register")
        data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "securepass123",
            "password_confirm": "differentpass",
            "first_name": "New",
            "last_name": "User",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_email(self, api_client, user):
        """Test registration with existing email."""
        url = reverse("register")
        data = {
            "email": user.email,
            "username": "anotheruser",
            "password": "securepass123",
            "password_confirm": "securepass123",
            "first_name": "New",
            "last_name": "User",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserLogin:
    """Test user login endpoint."""

    def test_login_success(self, api_client, user):
        """Test successful login."""
        url = reverse("login")
        data = {"email": user.email, "password": "testpass123"}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_invalid_password(self, api_client, user):
        """Test login with wrong password."""
        url = reverse("login")
        data = {"email": user.email, "password": "wrongpassword"}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, api_client):
        """Test login with non-existent user."""
        url = reverse("login")
        data = {"email": "nonexistent@example.com", "password": "somepassword"}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserProfile:
    """Test user profile endpoints."""

    def test_get_profile_authenticated(self, auth_client, user):
        """Test getting profile when authenticated."""
        url = reverse("profile")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email

    def test_get_profile_unauthenticated(self, api_client):
        """Test getting profile when not authenticated."""
        url = reverse("profile")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile(self, auth_client, user):
        """Test updating user profile."""
        url = reverse("profile")
        data = {"first_name": "Updated", "last_name": "Name"}
        response = auth_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Updated"
