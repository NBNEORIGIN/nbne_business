"""
Tenant middleware — resolves the current tenant for every request.

Resolution order:
1. Authenticated user → user.tenant
2. X-Tenant-Slug header (sent by frontend proxy)
3. ?tenant= query param (backward compat)
4. First tenant in DB (fallback)
"""
from tenants.models import TenantSettings


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = None

        # 1. From authenticated user
        if hasattr(request, 'user') and request.user.is_authenticated:
            tenant = getattr(request.user, 'tenant', None)

        # 2. From X-Tenant-Slug header
        if not tenant:
            slug = request.META.get('HTTP_X_TENANT_SLUG', '')
            if slug:
                tenant = TenantSettings.objects.filter(slug=slug).first()

        # 3. From ?tenant= query param
        if not tenant:
            slug = request.GET.get('tenant', '')
            if slug:
                tenant = TenantSettings.objects.filter(slug=slug).first()

        # 4. Fallback to first tenant
        if not tenant:
            tenant = TenantSettings.objects.first()

        request.tenant = tenant
        return self.get_response(request)
