from django.db import models


class Interview(models.Model):
    """Interview model for tracking interview rounds."""
    
    TYPE_CHOICES = [
        ('phone', 'Phone Screen'),
        ('technical', 'Technical'),
        ('behavioral', 'Behavioral'),
        ('coding', 'Coding Challenge'),
        ('system_design', 'System Design'),
        ('onsite', 'On-site'),
        ('hr', 'HR/Final'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
        ('no_show', 'No Show'),
    ]
    
    OUTCOME_CHOICES = [
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
    ]

    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.CASCADE,
        related_name='interviews'
    )
    
    # Interview details
    round_number = models.PositiveSmallIntegerField(default=1)
    interview_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='phone')
    
    # Scheduling
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=60)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Meeting info
    meeting_link = models.URLField(blank=True)
    meeting_location = models.CharField(max_length=255, blank=True)
    
    # Interviewers
    interviewer_names = models.CharField(max_length=500, blank=True)
    interviewer_titles = models.CharField(max_length=500, blank=True)
    
    # Status & outcome
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    outcome = models.CharField(max_length=10, choices=OUTCOME_CHOICES, default='pending')
    
    # Notes
    preparation_notes = models.TextField(blank=True)
    post_interview_notes = models.TextField(blank=True)
    questions_asked = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Interview'
        verbose_name_plural = 'Interviews'
        ordering = ['scheduled_at']

    def __str__(self):
        return f"{self.application.job_title} - Round {self.round_number} ({self.interview_type})"

    @property
    def is_upcoming(self):
        """Check if interview is in the future."""
        from django.utils import timezone
        return self.scheduled_at > timezone.now() and self.status == 'scheduled'
