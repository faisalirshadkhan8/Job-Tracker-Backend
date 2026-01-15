from django.conf import settings
from django.db import models


class Company(models.Model):
    """Company model for tracking organizations."""

    SIZE_CHOICES = [
        ("startup", "Startup (1-50)"),
        ("small", "Small (51-200)"),
        ("medium", "Medium (201-1000)"),
        ("large", "Large (1001-5000)"),
        ("enterprise", "Enterprise (5000+)"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="companies")
    name = models.CharField(max_length=200)
    website = models.URLField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=200, blank=True)
    size = models.CharField(max_length=20, choices=SIZE_CHOICES, blank=True)
    glassdoor_rating = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        ordering = ["name"]
        # Each user can have only one entry per company name
        unique_together = ["user", "name"]

    def __str__(self):
        return self.name

    @property
    def application_count(self):
        return self.applications.count()
