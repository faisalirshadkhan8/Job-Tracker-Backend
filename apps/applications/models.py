from django.db import models
from django.conf import settings


class ResumeVersion(models.Model):
    """Resume version management for users."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resumes'
    )
    version_name = models.CharField(max_length=100)  # e.g., "Backend Focus", "Full Stack"
    file_url = models.URLField(blank=True)  # Cloudinary URL
    file_name = models.CharField(max_length=255, blank=True)
    cloudinary_public_id = models.CharField(max_length=255, blank=True)  # For deletion
    file_size = models.PositiveIntegerField(default=0)  # File size in bytes
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Resume Version'
        verbose_name_plural = 'Resume Versions'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.version_name}"

    def save(self, *args, **kwargs):
        # Ensure only one default resume per user
        if self.is_default:
            ResumeVersion.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Delete file from Cloudinary when model is deleted
        if self.cloudinary_public_id:
            try:
                from services.cloudinary_service import CloudinaryService
                CloudinaryService.delete_file(self.cloudinary_public_id)
            except Exception:
                pass  # Continue even if Cloudinary delete fails
        super().delete(*args, **kwargs)


class Application(models.Model):
    """Job Application model - the core entity."""
    
    STATUS_CHOICES = [
        ('wishlist', 'Wishlist'),
        ('applied', 'Applied'),
        ('screening', 'Screening'),
        ('interviewing', 'Interviewing'),
        ('offer', 'Offer Received'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
        ('ghosted', 'Ghosted'),
    ]
    
    WORK_TYPE_CHOICES = [
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
        ('onsite', 'On-site'),
    ]
    
    SOURCE_CHOICES = [
        ('linkedin', 'LinkedIn'),
        ('indeed', 'Indeed'),
        ('glassdoor', 'Glassdoor'),
        ('company_site', 'Company Website'),
        ('referral', 'Referral'),
        ('recruiter', 'Recruiter'),
        ('job_fair', 'Job Fair'),
        ('other', 'Other'),
    ]
    
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    # Relationships
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='applications'
    )
    resume_version = models.ForeignKey(
        ResumeVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications'
    )

    # Job details
    job_title = models.CharField(max_length=200)
    job_url = models.URLField(blank=True)
    job_description = models.TextField(blank=True)
    
    # Application status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Work details
    work_type = models.CharField(max_length=10, choices=WORK_TYPE_CHOICES, blank=True)
    location = models.CharField(max_length=200, blank=True)
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    
    # Source & tracking
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='linkedin')
    referrer_name = models.CharField(max_length=100, blank=True)  # If referral
    cover_letter = models.TextField(blank=True)
    
    # Important dates
    applied_date = models.DateField(null=True, blank=True)
    response_date = models.DateField(null=True, blank=True)
    
    # Next action tracking
    next_action = models.CharField(max_length=255, blank=True)
    next_action_date = models.DateField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.job_title} at {self.company.name}"

    @property
    def days_since_applied(self):
        """Calculate days since application was submitted."""
        if self.applied_date:
            from django.utils import timezone
            today = timezone.now().date()
            return (today - self.applied_date).days
        return None

    @property
    def has_response(self):
        """Check if application has received a response."""
        return self.response_date is not None


class Note(models.Model):
    """Notes related to a job application."""
    
    NOTE_TYPE_CHOICES = [
        ('general', 'General'),
        ('follow_up', 'Follow Up'),
        ('feedback', 'Feedback'),
        ('research', 'Company Research'),
        ('preparation', 'Interview Prep'),
    ]

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    content = models.TextField()
    note_type = models.CharField(max_length=20, choices=NOTE_TYPE_CHOICES, default='general')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Note'
        verbose_name_plural = 'Notes'
        ordering = ['-created_at']

    def __str__(self):
        return f"Note for {self.application.job_title} - {self.note_type}"
