"""
Tests for Interview CRUD operations.
"""

import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework import status


@pytest.mark.django_db
class TestInterviewList:
    """Test interview list endpoint."""
    
    def test_list_interviews(self, auth_client, interview):
        """Test listing interviews."""
        url = reverse('interview-list')
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_list_interviews_unauthenticated(self, api_client):
        """Test listing interviews without auth."""
        url = reverse('interview-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestInterviewCreate:
    """Test interview creation."""
    
    def test_create_interview(self, auth_client, application):
        """Test creating an interview."""
        url = reverse('interview-list')
        scheduled = (timezone.now() + timedelta(days=3)).isoformat()
        data = {
            'application': application.id,
            'interview_type': 'technical',
            'scheduled_at': scheduled,
            'duration_minutes': 90,
            'interviewer_name': 'Jane Smith',
            'notes': 'Technical interview with team lead'
        }
        response = auth_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['interview_type'] == 'technical'
    
    def test_create_interview_minimal(self, auth_client, application):
        """Test creating interview with minimal data."""
        url = reverse('interview-list')
        scheduled = (timezone.now() + timedelta(days=1)).isoformat()
        data = {
            'application': application.id,
            'interview_type': 'phone',
            'scheduled_at': scheduled
        }
        response = auth_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestInterviewSpecialEndpoints:
    """Test interview special endpoints (upcoming, today)."""
    
    def test_upcoming_interviews(self, auth_client, application):
        """Test getting upcoming interviews."""
        from apps.interviews.models import Interview
        
        # Create future interview
        Interview.objects.create(
            application=application,
            interview_type='onsite',
            scheduled_at=timezone.now() + timedelta(days=5)
        )
        
        url = reverse('interview-upcoming')
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
    
    def test_today_interviews(self, auth_client, application):
        """Test getting today's interviews."""
        from apps.interviews.models import Interview
        
        # Create interview for today
        Interview.objects.create(
            application=application,
            interview_type='phone',
            scheduled_at=timezone.now() + timedelta(hours=2)
        )
        
        url = reverse('interview-today')
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestInterviewOutcome:
    """Test interview outcome updates."""
    
    def test_update_outcome(self, auth_client, interview):
        """Test updating interview outcome."""
        url = reverse('interview-update-outcome', kwargs={'pk': interview.id})
        data = {'outcome': 'passed'}
        response = auth_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
    
    def test_invalid_outcome(self, auth_client, interview):
        """Test that invalid outcome is rejected."""
        url = reverse('interview-update-outcome', kwargs={'pk': interview.id})
        data = {'outcome': 'invalid'}
        response = auth_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
