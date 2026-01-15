"""
Tests for Application CRUD operations.
"""

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestApplicationList:
    """Test application list endpoint."""
    
    def test_list_applications(self, auth_client, application):
        """Test listing applications."""
        url = reverse('application-list')
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_list_applications_unauthenticated(self, api_client):
        """Test listing applications without auth."""
        url = reverse('application-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestApplicationCreate:
    """Test application creation."""
    
    def test_create_application(self, auth_client, company):
        """Test creating an application."""
        url = reverse('application-list')
        data = {
            'company': company.id,
            'job_title': 'Backend Developer',
            'job_url': 'https://company.com/jobs/2',
            'status': 'applied',
            'source': 'indeed'
        }
        response = auth_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['job_title'] == 'Backend Developer'
    
    def test_create_application_with_salary(self, auth_client, company):
        """Test creating application with salary range."""
        url = reverse('application-list')
        data = {
            'company': company.id,
            'job_title': 'Senior Engineer',
            'status': 'applied',
            'salary_min': 150000,
            'salary_max': 200000
        }
        response = auth_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['salary_min'] == 150000


@pytest.mark.django_db
class TestApplicationStatus:
    """Test application status updates."""
    
    def test_update_status(self, auth_client, application):
        """Test updating application status."""
        url = reverse('application-detail', kwargs={'pk': application.id})
        data = {'status': 'interviewing'}
        response = auth_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'interviewing'
    
    def test_status_choices(self, auth_client, application):
        """Test that invalid status is rejected."""
        url = reverse('application-detail', kwargs={'pk': application.id})
        data = {'status': 'invalid_status'}
        response = auth_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestApplicationFiltering:
    """Test application filtering."""
    
    def test_filter_by_status(self, auth_client, user, company):
        """Test filtering by status."""
        from apps.applications.models import Application
        
        Application.objects.create(
            user=user, company=company,
            job_title='Job 1', status='applied'
        )
        Application.objects.create(
            user=user, company=company,
            job_title='Job 2', status='rejected'
        )
        
        url = reverse('application-list') + '?status=applied'
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert all(a['status'] == 'applied' for a in results)
    
    def test_filter_by_company(self, auth_client, user, company):
        """Test filtering by company."""
        from apps.applications.models import Application
        from apps.companies.models import Company
        
        other_company = Company.objects.create(user=user, name='Other Co')
        Application.objects.create(
            user=user, company=company,
            job_title='Job at Test', status='applied'
        )
        Application.objects.create(
            user=user, company=other_company,
            job_title='Job at Other', status='applied'
        )
        
        url = reverse('application-list') + f'?company={company.id}'
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert all(a['company'] == company.id for a in results)


@pytest.mark.django_db
class TestApplicationIsolation:
    """Test that users can only see their own applications."""
    
    def test_cannot_see_other_user_applications(self, auth_client_user2, application):
        """Test user cannot see other user's applications."""
        url = reverse('application-detail', kwargs={'pk': application.id})
        response = auth_client_user2.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_cannot_update_other_user_applications(self, auth_client_user2, application):
        """Test user cannot update other user's applications."""
        url = reverse('application-detail', kwargs={'pk': application.id})
        data = {'status': 'rejected'}
        response = auth_client_user2.patch(url, data, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND
