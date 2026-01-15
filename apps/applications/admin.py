from django.contrib import admin
from .models import Application, Note, ResumeVersion


class NoteInline(admin.TabularInline):
    model = Note
    extra = 0


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['job_title', 'company', 'user', 'status', 'priority', 'applied_date', 'updated_at']
    list_filter = ['status', 'priority', 'work_type', 'source', 'applied_date']
    search_fields = ['job_title', 'company__name', 'user__email']
    ordering = ['-updated_at']
    inlines = [NoteInline]
    date_hierarchy = 'applied_date'


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['application', 'note_type', 'created_at']
    list_filter = ['note_type', 'created_at']


@admin.register(ResumeVersion)
class ResumeVersionAdmin(admin.ModelAdmin):
    list_display = ['user', 'version_name', 'is_default', 'created_at']
    list_filter = ['is_default', 'created_at']
