"""
Tests for Celery async AI tasks.
"""

import pytest
from django.urls import reverse
from unittest.mock import patch, MagicMock
from apps.ai.models import AITask, GeneratedContent


@pytest.fixture
def mock_celery_task():
    """Mock Celery task to avoid actually queuing tasks."""
    with patch('apps.ai.views.generate_cover_letter_task') as mock:
        mock.delay = MagicMock()
        yield mock


@pytest.fixture
def ai_task(user):
    """Create a test AI task."""
    return AITask.objects.create(
        user=user,
        task_type='cover_letter',
        status='pending',
        input_params={
            'company_name': 'Test Corp',
            'job_title': 'Developer',
            'tone': 'professional'
        }
    )


@pytest.fixture
def completed_ai_task(user):
    """Create a completed AI task."""
    from django.utils import timezone
    return AITask.objects.create(
        user=user,
        task_type='cover_letter',
        status='completed',
        input_params={
            'company_name': 'Test Corp',
            'job_title': 'Developer',
        },
        result={
            'cover_letter': 'Dear Hiring Manager...',
            'model': 'llama-3.3-70b-versatile',
            'tokens_used': 500,
        },
        started_at=timezone.now(),
        completed_at=timezone.now()
    )


@pytest.mark.django_db
class TestAITaskModel:
    """Tests for AITask model."""

    def test_create_ai_task(self, user):
        """Test creating an AI task."""
        task = AITask.objects.create(
            user=user,
            task_type='cover_letter',
            status='pending'
        )
        assert task.id is not None
        assert task.status == 'pending'
        assert task.task_type == 'cover_letter'

    def test_ai_task_duration_property(self, user):
        """Test duration calculation."""
        from django.utils import timezone
        from datetime import timedelta

        task = AITask.objects.create(
            user=user,
            task_type='job_match',
            status='completed',
            started_at=timezone.now(),
            completed_at=timezone.now() + timedelta(seconds=5)
        )
        assert task.duration == pytest.approx(5, abs=0.1)

    def test_ai_task_str(self, user):
        """Test string representation."""
        task = AITask.objects.create(
            user=user,
            task_type='cover_letter',
            status='pending'
        )
        assert 'Cover Letter' in str(task)
        assert 'pending' in str(task)


@pytest.mark.django_db
class TestAsyncCoverLetterEndpoint:
    """Tests for async cover letter generation."""

    @patch('apps.ai.views.should_use_async', return_value=True)
    @patch('apps.ai.tasks.generate_cover_letter_task.delay')
    def test_async_cover_letter_returns_202(self, mock_delay, mock_async, auth_client, user):
        """Test async mode returns 202 Accepted with task_id."""
        url = reverse('cover-letter-generate')
        data = {
            'job_description': 'x' * 100,
            'resume_text': 'Experienced developer with Python skills.',
            'company_name': 'Tech Corp',
            'job_title': 'Senior Developer',
            'async_mode': True,
        }

        response = auth_client.post(url, data, format='json')

        assert response.status_code == 202
        assert 'task_id' in response.data
        assert response.data['status'] == 'pending'
        assert 'message' in response.data

    @patch('apps.ai.views.should_use_async', return_value=True)
    @patch('apps.ai.tasks.generate_cover_letter_task.delay')
    def test_async_creates_task_record(self, mock_delay, mock_async, auth_client, user):
        """Test async mode creates AITask in database."""
        url = reverse('cover-letter-generate')
        data = {
            'job_description': 'x' * 100,
            'resume_text': 'Experienced developer.',
            'company_name': 'Tech Corp',
            'job_title': 'Developer',
            'async_mode': True,
        }

        response = auth_client.post(url, data, format='json')

        task_id = response.data['task_id']
        task = AITask.objects.get(id=task_id)
        assert task.user == user
        assert task.task_type == 'cover_letter'
        assert task.status == 'pending'

    @patch('apps.ai.views.should_use_async', return_value=True)
    @patch('apps.ai.tasks.generate_cover_letter_task.delay')
    def test_celery_task_called_with_correct_args(self, mock_delay, mock_async, auth_client, user):
        """Test Celery task is called with correct arguments."""
        url = reverse('cover-letter-generate')
        data = {
            'job_description': 'x' * 100,
            'resume_text': 'Developer resume.',
            'company_name': 'Acme Inc',
            'job_title': 'Backend Dev',
            'tone': 'enthusiastic',
            'async_mode': True,
        }

        auth_client.post(url, data, format='json')

        mock_delay.assert_called_once()
        call_kwargs = mock_delay.call_args.kwargs
        assert 'task_id' in call_kwargs
        assert call_kwargs['company_name'] == 'Acme Inc'
        assert call_kwargs['job_title'] == 'Backend Dev'
        assert call_kwargs['tone'] == 'enthusiastic'


@pytest.mark.django_db
class TestAsyncJobMatchEndpoint:
    """Tests for async job match analysis."""

    @patch('apps.ai.views.should_use_async', return_value=True)
    @patch('apps.ai.tasks.analyze_job_match_task.delay')
    def test_async_job_match_returns_202(self, mock_delay, mock_async, auth_client):
        """Test async job match returns 202."""
        url = reverse('job-match-analyze')
        data = {
            'job_description': 'x' * 100,
            'resume_text': 'Python developer with 5 years experience.',
            'async_mode': True,
        }

        response = auth_client.post(url, data, format='json')

        assert response.status_code == 202
        assert 'task_id' in response.data


@pytest.mark.django_db
class TestAsyncInterviewQuestionsEndpoint:
    """Tests for async interview questions."""

    @patch('apps.ai.views.should_use_async', return_value=True)
    @patch('apps.ai.tasks.generate_interview_questions_task.delay')
    def test_async_interview_questions_returns_202(self, mock_delay, mock_async, auth_client):
        """Test async interview questions returns 202."""
        url = reverse('interview-questions-generate')
        data = {
            'job_description': 'x' * 100,
            'company_name': 'BigTech',
            'job_title': 'Engineer',
            'async_mode': True,
        }

        response = auth_client.post(url, data, format='json')

        assert response.status_code == 202
        assert 'task_id' in response.data


@pytest.mark.django_db
class TestAITaskViewSet:
    """Tests for AI Task management endpoints."""

    def test_list_tasks(self, auth_client, ai_task):
        """Test listing user's AI tasks."""
        url = reverse('ai-tasks-list')
        response = auth_client.get(url)

        assert response.status_code == 200
        data = response.data.get('results', response.data)
        assert len(data) >= 1

    def test_retrieve_task(self, auth_client, ai_task):
        """Test retrieving a specific task."""
        url = reverse('ai-tasks-detail', args=[ai_task.id])
        response = auth_client.get(url)

        assert response.status_code == 200
        assert response.data['id'] == ai_task.id
        assert response.data['status'] == 'pending'

    def test_retrieve_completed_task_includes_result(self, auth_client, completed_ai_task):
        """Test completed task includes result."""
        url = reverse('ai-tasks-detail', args=[completed_ai_task.id])
        response = auth_client.get(url)

        assert response.status_code == 200
        assert response.data['status'] == 'completed'
        assert 'result' in response.data
        assert 'cover_letter' in response.data['result']

    def test_pending_tasks_endpoint(self, auth_client, ai_task, completed_ai_task):
        """Test listing only pending tasks."""
        url = reverse('ai-tasks-pending')
        response = auth_client.get(url)

        assert response.status_code == 200
        # Should only include pending task, not completed
        task_ids = [t['id'] for t in response.data]
        assert ai_task.id in task_ids
        assert completed_ai_task.id not in task_ids

    def test_cancel_pending_task(self, auth_client, ai_task):
        """Test cancelling a pending task."""
        url = reverse('ai-tasks-cancel', args=[ai_task.id])
        response = auth_client.post(url)

        assert response.status_code == 200
        assert response.data['status'] == 'cancelled'

        ai_task.refresh_from_db()
        assert ai_task.status == 'failed'
        assert ai_task.error_message == 'Cancelled by user'

    def test_cannot_cancel_completed_task(self, auth_client, completed_ai_task):
        """Test cannot cancel already completed task."""
        url = reverse('ai-tasks-cancel', args=[completed_ai_task.id])
        response = auth_client.post(url)

        assert response.status_code == 400
        assert 'error' in response.data

    def test_delete_task(self, auth_client, completed_ai_task):
        """Test deleting a task."""
        url = reverse('ai-tasks-detail', args=[completed_ai_task.id])
        response = auth_client.delete(url)

        assert response.status_code == 204
        assert not AITask.objects.filter(id=completed_ai_task.id).exists()

    def test_cannot_access_other_users_task(self, auth_client, another_user):
        """Test user cannot access another user's task."""
        other_task = AITask.objects.create(
            user=another_user,
            task_type='cover_letter',
            status='pending'
        )

        url = reverse('ai-tasks-detail', args=[other_task.id])
        response = auth_client.get(url)

        assert response.status_code == 404


@pytest.mark.django_db
class TestSyncModeStillWorks:
    """Ensure sync mode still works when async is disabled."""

    @patch('apps.ai.views.should_use_async', return_value=False)
    @patch('services.groq_service.GroqService.generate_cover_letter')
    def test_sync_cover_letter_returns_200(self, mock_groq, mock_async, auth_client):
        """Test sync mode returns 200 with content."""
        mock_groq.return_value = {
            'cover_letter': 'Dear Hiring Manager, I am excited...',
            'model': 'llama-3.3-70b-versatile',
            'usage': {'total_tokens': 500}
        }

        url = reverse('cover-letter-generate')
        data = {
            'job_description': 'x' * 100,
            'resume_text': 'Experienced developer.',
            'company_name': 'Tech Corp',
            'job_title': 'Developer',
            'async_mode': False,
        }

        response = auth_client.post(url, data, format='json')

        assert response.status_code == 200
        assert 'cover_letter' in response.data
        assert 'task_id' not in response.data
