"""
Test configuration and fixtures for Job Application Tracker.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create and return a test user."""
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def user2(db):
    """Create and return a second test user."""
    return User.objects.create_user(
        username='testuser2',
        email='testuser2@example.com',
        password='testpass123',
        first_name='Test2',
        last_name='User2'
    )


@pytest.fixture
def another_user(db):
    """Create and return another test user (alias for user2)."""
    return User.objects.create_user(
        username='anotheruser',
        email='anotheruser@example.com',
        password='testpass123',
        first_name='Another',
        last_name='User'
    )


@pytest.fixture
def auth_client(user):
    """Return an authenticated API client."""
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def auth_client_user2(user2):
    """Return an authenticated API client for user2."""
    client = APIClient()
    refresh = RefreshToken.for_user(user2)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def company(db, user):
    """Create and return a test company."""
    from apps.companies.models import Company
    return Company.objects.create(
        user=user,
        name='Test Company',
        website='https://testcompany.com',
        industry='Technology',
        size='51-200',
        location='San Francisco, CA'
    )


@pytest.fixture
def application(db, user, company):
    """Create and return a test application."""
    from apps.applications.models import Application
    return Application.objects.create(
        user=user,
        company=company,
        job_title='Software Engineer',
        job_url='https://testcompany.com/jobs/1',
        status='applied',
        source='linkedin',
        salary_min=100000,
        salary_max=150000
    )


@pytest.fixture
def interview(db, application):
    """Create and return a test interview."""
    from apps.interviews.models import Interview
    from django.utils import timezone
    from datetime import timedelta
    
    return Interview.objects.create(
        application=application,
        interview_type='phone',
        scheduled_at=timezone.now() + timedelta(days=1),
        duration_minutes=60,
        interviewer_names='John Doe',
        preparation_notes='Initial phone screen'
    )
