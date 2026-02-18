"""
Tenant settings endpoint alias — serves /api/tenant/
Returns per-tenant settings from TenantSettings model.
"""
from django.urls import path
from tenants.views import tenant_settings

urlpatterns = [
    path('', tenant_settings, name='tenant-settings'),
]
