"""
Tenant branding endpoint alias — serves /api/tenant/branding/
Returns per-tenant branding from TenantSettings model.
"""
from django.urls import path
from tenants.views import tenant_branding

urlpatterns = [
    path('', tenant_branding, name='tenant-branding'),
]
