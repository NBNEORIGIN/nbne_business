from django.contrib import admin
from .models import TenantSettings


@admin.register(TenantSettings)
class TenantSettingsAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'email', 'phone', 'currency']
