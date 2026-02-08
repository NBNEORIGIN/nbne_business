from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active_staff', 'is_active']
    list_filter = ['role', 'is_active', 'is_active_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('NBNE Role & Profile', {
            'fields': ('role', 'phone', 'bio', 'avatar_initials', 'is_active_staff'),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('NBNE Role & Profile', {
            'fields': ('role', 'first_name', 'last_name', 'email', 'phone'),
        }),
    )
