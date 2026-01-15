"""
Two-Factor Authentication Admin Configuration.
"""

from django.contrib import admin

from .models import TwoFactorDevice, BackupCode


@admin.register(TwoFactorDevice)
class TwoFactorDeviceAdmin(admin.ModelAdmin):
    """Admin for 2FA devices."""
    
    list_display = ['user', 'is_enabled', 'is_verified', 'verified_at', 'last_used_at']
    list_filter = ['is_enabled', 'is_verified', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['id', 'secret', 'is_verified', 'verified_at', 'last_used_at', 'created_at']
    
    fieldsets = [
        (None, {
            'fields': ['id', 'user', 'is_enabled', 'is_verified']
        }),
        ('Security', {
            'fields': ['secret'],
            'classes': ['collapse'],
        }),
        ('Timestamps', {
            'fields': ['verified_at', 'last_used_at', 'created_at']
        }),
    ]
    
    def has_add_permission(self, request):
        return False  # Devices are created through API


@admin.register(BackupCode)
class BackupCodeAdmin(admin.ModelAdmin):
    """Admin for backup codes."""
    
    list_display = ['device', 'is_used', 'used_at', 'created_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['device__user__email']
    readonly_fields = ['id', 'device', 'code_hash', 'is_used', 'used_at', 'created_at']
    
    def has_add_permission(self, request):
        return False  # Codes are generated through API
    
    def has_change_permission(self, request, obj=None):
        return False
