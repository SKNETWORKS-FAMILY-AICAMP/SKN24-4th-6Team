from django.contrib import admin

from core.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'nickname', 'is_verified', 'is_admin', 'created_at']
    list_filter = ['is_verified', 'is_admin']
    search_fields = ['email', 'nickname']
    ordering = ['-created_at']
    readonly_fields = ['user_id', 'created_at']
