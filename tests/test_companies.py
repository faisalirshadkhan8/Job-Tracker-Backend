"""
Tests for Company CRUD operations.
"""

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestCompanyList:
    """Test company list endpoint."""
    
    def test_list_companies_authenticated(self, auth_client, company):
        """Test listing companies when authenticated."""
        url = reverse('company-list')
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 1
    
    def test_list_companies_unauthenticated(self, api_client):
        """Test listing companies when not authenticated."""
        url = reverse('company-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_only_own_companies(self, auth_client, auth_client_user2, company, user2):
        """Test that users only see their own companies."""
        from apps.companies.models import Company
        
        # Create company for user2
        Company.objects.create(
            user=user2,
            name='User2 Company',
            industry='Finance'
        )
        
        # User1 should only see their company
        url = reverse('company-list')
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert all(c['name'] != 'User2 Company' for c in results)


@pytest.mark.django_db
class TestCompanyCreate:
    """Test company creation endpoint."""
    
    def test_create_company_success(self, auth_client):
        """Test creating a company."""
        url = reverse('company-list')
        data = {
            'name': 'New Company',
            'website': 'https://newcompany.com',
            'industry': 'Healthcare',
            'size': 'medium',
            'location': 'New York, NY'
        }
        response = auth_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Company'
    
    def test_create_company_minimal(self, auth_client):
        """Test creating a company with minimal data."""
        url = reverse('company-list')
        data = {'name': 'Minimal Company'}
        response = auth_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_create_company_missing_name(self, auth_client):
        """Test creating a company without name fails."""
        url = reverse('company-list')
        data = {'website': 'https://noname.com'}
        response = auth_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCompanyDetail:
    """Test company detail/update/delete endpoints."""
    
    def test_get_company_detail(self, auth_client, company):
        """Test getting company details."""
        url = reverse('company-detail', kwargs={'pk': company.id})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == company.name
    
    def test_update_company(self, auth_client, company):
        """Test updating a company."""
        url = reverse('company-detail', kwargs={'pk': company.id})
        data = {'name': 'Updated Company Name'}
        response = auth_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Company Name'
    
    def test_delete_company(self, auth_client, company):
        """Test deleting a company."""
        url = reverse('company-detail', kwargs={'pk': company.id})
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_cannot_access_other_user_company(self, auth_client_user2, company):
        """Test that users cannot access other users' companies."""
        url = reverse('company-detail', kwargs={'pk': company.id})
        response = auth_client_user2.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCompanyFiltering:
    """Test company filtering."""
    
    def test_filter_by_industry(self, auth_client, user):
        """Test filtering companies by industry."""
        from apps.companies.models import Company
        
        Company.objects.create(user=user, name='Tech Co', industry='Technology')
        Company.objects.create(user=user, name='Finance Co', industry='Finance')
        
        url = reverse('company-list') + '?industry=Technology'
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert all(c['industry'] == 'Technology' for c in results)
    
    def test_search_by_name(self, auth_client, user):
        """Test searching companies by name."""
        from apps.companies.models import Company
        
        Company.objects.create(user=user, name='Acme Corporation', industry='Technology')
        Company.objects.create(user=user, name='Beta Inc', industry='Finance')
        
        url = reverse('company-list') + '?search=Acme'
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert any('Acme' in c['name'] for c in results)
