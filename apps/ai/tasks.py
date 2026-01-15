"""
Celery Tasks for AI Features.

These tasks run asynchronously in background workers,
allowing instant API responses while AI processing continues.
"""

import json
import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_kwargs={'max_retries': 3},
    soft_time_limit=120,
    time_limit=180,
)
def generate_cover_letter_task(
    self,
    task_id: int,
    job_description: str,
    resume_text: str,
    company_name: str,
    job_title: str,
    tone: str = 'professional'
):
    """
    Generate a cover letter asynchronously.
    
    Args:
        task_id: AITask model ID for status updates
        job_description: Sanitized job description
        resume_text: Sanitized resume content
        company_name: Company name
        job_title: Position title
        tone: Writing tone (professional, enthusiastic, formal)
    """
    from apps.ai.models import AITask, GeneratedContent
    from services.groq_service import GroqService
    
    task = AITask.objects.get(id=task_id)
    
    try:
        # Update status to processing
        task.status = 'processing'
        task.celery_task_id = self.request.id
        task.started_at = timezone.now()
        task.save(update_fields=['status', 'celery_task_id', 'started_at'])
        
        # Generate content
        result = GroqService.generate_cover_letter(
            job_description=job_description,
            resume_text=resume_text,
            company_name=company_name,
            job_title=job_title,
            tone=tone
        )
        
        # Save generated content to history
        generated = GeneratedContent.objects.create(
            user=task.user,
            application_id=task.application_id,
            content_type='cover_letter',
            input_job_description=job_description,
            input_resume_text=resume_text,
            input_company_name=company_name,
            input_job_title=job_title,
            input_params={'tone': tone},
            output_content=result['cover_letter'],
            output_metadata=result.get('usage', {}),
            model_used=result['model'],
            tokens_used=result.get('usage', {}).get('total_tokens', 0)
        )
        
        # Update task as completed
        task.status = 'completed'
        task.result = {
            'cover_letter': result['cover_letter'],
            'model': result['model'],
            'tokens_used': result.get('usage', {}).get('total_tokens', 0),
            'generated_content_id': generated.id
        }
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'result', 'completed_at'])
        
        logger.info(f"Cover letter task {task_id} completed successfully")
        return task.result
        
    except Exception as e:
        logger.error(f"Cover letter task {task_id} failed: {str(e)}")
        task.status = 'failed'
        task.error_message = str(e)
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'error_message', 'completed_at'])
        raise


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_kwargs={'max_retries': 3},
    soft_time_limit=120,
    time_limit=180,
)
def analyze_job_match_task(
    self,
    task_id: int,
    job_description: str,
    resume_text: str
):
    """
    Analyze job match asynchronously.
    
    Args:
        task_id: AITask model ID for status updates
        job_description: Sanitized job description
        resume_text: Sanitized resume content
    """
    from apps.ai.models import AITask, GeneratedContent
    from services.groq_service import GroqService
    
    task = AITask.objects.get(id=task_id)
    
    try:
        task.status = 'processing'
        task.celery_task_id = self.request.id
        task.started_at = timezone.now()
        task.save(update_fields=['status', 'celery_task_id', 'started_at'])
        
        result = GroqService.analyze_job_match(
            job_description=job_description,
            resume_text=resume_text
        )
        
        # Parse analysis if JSON
        analysis_content = result['analysis']
        try:
            analysis_content = json.loads(analysis_content)
        except (json.JSONDecodeError, TypeError):
            pass
        
        generated = GeneratedContent.objects.create(
            user=task.user,
            application_id=task.application_id,
            content_type='job_match',
            input_job_description=job_description,
            input_resume_text=resume_text,
            output_content=result['analysis'],
            output_metadata=result.get('usage', {}),
            model_used=result['model'],
            tokens_used=result.get('usage', {}).get('total_tokens', 0)
        )
        
        task.status = 'completed'
        task.result = {
            'analysis': analysis_content,
            'model': result['model'],
            'tokens_used': result.get('usage', {}).get('total_tokens', 0),
            'generated_content_id': generated.id
        }
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'result', 'completed_at'])
        
        logger.info(f"Job match task {task_id} completed successfully")
        return task.result
        
    except Exception as e:
        logger.error(f"Job match task {task_id} failed: {str(e)}")
        task.status = 'failed'
        task.error_message = str(e)
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'error_message', 'completed_at'])
        raise


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_kwargs={'max_retries': 3},
    soft_time_limit=120,
    time_limit=180,
)
def generate_interview_questions_task(
    self,
    task_id: int,
    job_description: str,
    company_name: str,
    job_title: str,
    question_count: int = 10
):
    """
    Generate interview questions asynchronously.
    
    Args:
        task_id: AITask model ID for status updates
        job_description: Sanitized job description
        company_name: Company name
        job_title: Position title
        question_count: Number of questions to generate
    """
    from apps.ai.models import AITask, GeneratedContent
    from services.groq_service import GroqService
    
    task = AITask.objects.get(id=task_id)
    
    try:
        task.status = 'processing'
        task.celery_task_id = self.request.id
        task.started_at = timezone.now()
        task.save(update_fields=['status', 'celery_task_id', 'started_at'])
        
        result = GroqService.generate_interview_questions(
            job_description=job_description,
            company_name=company_name,
            job_title=job_title,
            question_count=question_count
        )
        
        generated = GeneratedContent.objects.create(
            user=task.user,
            application_id=task.application_id,
            content_type='interview_questions',
            input_job_description=job_description,
            input_company_name=company_name,
            input_job_title=job_title,
            input_params={'question_count': question_count},
            output_content=result['questions'],
            output_metadata=result.get('usage', {}),
            model_used=result['model'],
            tokens_used=result.get('usage', {}).get('total_tokens', 0)
        )
        
        task.status = 'completed'
        task.result = {
            'questions': result['questions'],
            'model': result['model'],
            'tokens_used': result.get('usage', {}).get('total_tokens', 0),
            'generated_content_id': generated.id
        }
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'result', 'completed_at'])
        
        logger.info(f"Interview questions task {task_id} completed successfully")
        return task.result
        
    except Exception as e:
        logger.error(f"Interview questions task {task_id} failed: {str(e)}")
        task.status = 'failed'
        task.error_message = str(e)
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'error_message', 'completed_at'])
        raise


@shared_task
def cleanup_stale_tasks():
    """
    Clean up tasks that have been pending for too long.
    Runs periodically via Celery Beat.
    """
    from apps.ai.models import AITask
    from datetime import timedelta
    
    # Mark tasks pending for more than 30 minutes as failed
    stale_threshold = timezone.now() - timedelta(minutes=30)
    stale_tasks = AITask.objects.filter(
        status__in=['pending', 'processing'],
        created_at__lt=stale_threshold
    )
    
    count = stale_tasks.update(
        status='failed',
        error_message='Task timed out',
        completed_at=timezone.now()
    )
    
    if count:
        logger.warning(f"Cleaned up {count} stale AI tasks")
    
    return count
