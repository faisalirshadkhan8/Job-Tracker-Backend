from django.contrib import admin

from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "industry", "size", "glassdoor_rating", "created_at"]
    list_filter = ["size", "industry", "created_at"]
    search_fields = ["name", "industry", "location"]
    ordering = ["name"]
