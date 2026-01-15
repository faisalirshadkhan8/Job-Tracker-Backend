"""
AI Models - Store generated content for history and analytics.
"""

from django.conf import settings
from django.db import models


class AITask(models.Model):
    """
    Tracks async AI task execution.
    Allows users to check status and retrieve results.
    """

    TASK_TYPES = [
        ("cover_letter", "Cover Letter"),
        ("job_match", "Job Match Analysis"),
        ("interview_questions", "Interview Questions"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_tasks")
    application = models.ForeignKey(
        "applications.Application", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_tasks"
    )

    task_type = models.CharField(max_length=30, choices=TASK_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Celery task reference
    celery_task_id = models.CharField(max_length=255, blank=True, null=True)

    # Input parameters (stored for reference)
    input_params = models.JSONField(default=dict)

    # Result or error
    result = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "AI Task"
        verbose_name_plural = "AI Tasks"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["celery_task_id"]),
        ]

    def __str__(self):
        return f"{self.get_task_type_display()} - {self.status} ({self.id})"

    @property
    def duration(self):
        """Calculate task duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class GeneratedContent(models.Model):
    """
    Stores AI-generated content for user history.
    Allows users to revisit and reuse generated content.
    """

    CONTENT_TYPES = [
        ("cover_letter", "Cover Letter"),
        ("job_match", "Job Match Analysis"),
        ("interview_questions", "Interview Questions"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="generated_contents")
    application = models.ForeignKey(
        "applications.Application", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_contents"
    )
    content_type = models.CharField(max_length=30, choices=CONTENT_TYPES)

    # Input data (stored for regeneration)
    input_job_description = models.TextField(blank=True)
    input_resume_text = models.TextField(blank=True)
    input_company_name = models.CharField(max_length=255, blank=True)
    input_job_title = models.CharField(max_length=255, blank=True)
    input_params = models.JSONField(default=dict, blank=True)  # Additional params

    # Generated output
    output_content = models.TextField()
    output_metadata = models.JSONField(default=dict, blank=True)  # Token usage, model, etc.

    # Metadata
    model_used = models.CharField(max_length=100)
    tokens_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    # User feedback
    is_favorite = models.BooleanField(default=False)
    rating = models.IntegerField(null=True, blank=True)  # 1-5 stars

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Generated Content"
        verbose_name_plural = "Generated Contents"

    def __str__(self):
        return f"{self.get_content_type_display()} - {self.input_job_title or 'Untitled'}"
