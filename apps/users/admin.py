from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "username", "first_name", "last_name", "is_staff", "created_at"]
    list_filter = ["is_staff", "is_superuser", "is_active", "preferred_work_type"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering = ["-created_at"]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Profile", {"fields": ("phone", "linkedin_url", "portfolio_url", "github_url")}),
        (
            "Job Preferences",
            {"fields": ("desired_role", "desired_salary_min", "desired_salary_max", "preferred_work_type")},
        ),
    )
