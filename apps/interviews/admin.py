from django.contrib import admin

from .models import Interview


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ["application", "round_number", "interview_type", "scheduled_at", "status", "outcome"]
    list_filter = ["interview_type", "status", "outcome", "scheduled_at"]
    search_fields = ["application__job_title", "application__company__name"]
    ordering = ["-scheduled_at"]
    date_hierarchy = "scheduled_at"
