"""
Tests for AI endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch, MagicMock


@pytest.mark.django_db
class TestCoverLetterGeneration:
    """Test cover letter generation endpoint."""
    
    def test_cover_letter_unauthenticated(self, api_client):
        """Test that cover letter requires auth."""
        url = reverse('cover-letter-generate')
        response = api_client.post(url, {}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_cover_letter_missing_fields(self, auth_client):
        """Test that required fields are validated."""
        url = reverse('cover-letter-generate')
        data = {'job_title': 'Engineer'}  # Missing required fields
        response = auth_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch('apps.ai.views.GroqService.generate_cover_letter')
    def test_cover_letter_success(self, mock_generate, auth_client):
        """Test successful cover letter generation."""
        mock_generate.return_value = {
            'cover_letter': 'Dear Hiring Manager...',
            'model': 'llama-3.3-70b-versatile',
            'usage': {'total_tokens': 500}
        }
        
        url = reverse('cover-letter-generate')
        data = {
            'job_description': 'We are looking for a software engineer with Python experience...',
            'resume_text': 'Experienced software engineer with 5 years of Python development...',
            'company_name': 'Tech Corp',
            'job_title': 'Software Engineer',
            'tone': 'professional',
            'save_to_history': False,
            'async_mode': False  # Force sync mode for testing
        }
        response = auth_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'cover_letter' in response.data


@pytest.mark.django_db
class TestJobMatchAnalysis:
    """Test job match analysis endpoint."""
    
    def test_job_match_unauthenticated(self, api_client):
        """Test that job match requires auth."""
        url = reverse('job-match-analyze')
        response = api_client.post(url, {}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @patch('apps.ai.views.GroqService.analyze_job_match')
    def test_job_match_success(self, mock_analyze, auth_client):
        """Test successful job match analysis."""
        mock_analyze.return_value = {
            'analysis': '{"match_score": 85, "matching_skills": ["Python"]}',
            'model': 'llama-3.3-70b-versatile',
            'usage': {'total_tokens': 300}
        }
        
        url = reverse('job-match-analyze')
        data = {
            'job_description': 'Looking for a Python developer with strong Django experience, REST APIs, testing, and cloud deployment skills.',
            'resume_text': 'Python developer with 5 years experience...',
            'save_to_history': False,
            'async_mode': False  # Force sync mode for testing
        }
        response = auth_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'analysis' in response.data


@pytest.mark.django_db
class TestInterviewQuestions:
    """Test interview questions endpoint."""
    
    def test_interview_questions_unauthenticated(self, api_client):
        """Test that interview questions requires auth."""
        url = reverse('interview-questions-generate')
        response = api_client.post(url, {}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @patch('apps.ai.views.GroqService.generate_interview_questions')
    def test_interview_questions_success(self, mock_generate, auth_client):
        """Test successful interview question generation."""
        mock_generate.return_value = {
            'questions': '1. Tell me about yourself...',
            'model': 'llama-3.3-70b-versatile',
            'usage': {'total_tokens': 400}
        }
        
        url = reverse('interview-questions-generate')
        data = {
            'job_description': 'Looking for a backend engineer experienced with Python, Django, PostgreSQL, Redis, and RESTful API design.',
            'company_name': 'Tech Corp',
            'job_title': 'Backend Engineer',
            'question_count': 10,
            'save_to_history': False,
            'async_mode': False  # Force sync mode for testing
        }
        response = auth_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'questions' in response.data


@pytest.mark.django_db
class TestAIHistory:
    """Test AI history endpoints."""
    
    def test_history_list_empty(self, auth_client):
        """Test empty history list."""
        url = reverse('ai-history-list')
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) == 0
    
    def test_history_isolation(self, auth_client, auth_client_user2, user):
        """Test users only see their own history."""
        from apps.ai.models import GeneratedContent
        
        GeneratedContent.objects.create(
            user=user,
            content_type='cover_letter',
            output_content='Test content',
            model_used='test-model'
        )
        
        # User2 should not see user1's history
        url = reverse('ai-history-list')
        response = auth_client_user2.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) == 0
