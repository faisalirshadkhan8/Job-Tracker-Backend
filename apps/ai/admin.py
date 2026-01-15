from django.contrib import admin

from .models import GeneratedContent


@admin.register(GeneratedContent)
class GeneratedContentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "content_type",
        "input_company_name",
        "input_job_title",
        "model_used",
        "tokens_used",
        "is_favorite",
        "created_at",
    ]
    list_filter = ["content_type", "model_used", "is_favorite", "created_at"]
    search_fields = ["input_company_name", "input_job_title", "user__email"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]
