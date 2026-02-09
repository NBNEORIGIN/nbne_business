from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def api_index(request):
    """Root endpoint listing all available API routes."""
    routes = {
        'api': 'NBNE Platform Rev 2 — API',
        'version': '2.0.0',
        'endpoints': {
            'auth': '/api/auth/',
            'audit': '/api/audit/',
        }
    }
    if settings.TENANTS_MODULE_ENABLED:
        routes['endpoints']['tenant'] = '/api/tenant/'
    if settings.BOOKINGS_MODULE_ENABLED:
        routes['endpoints']['bookings'] = '/api/bookings/'
    if settings.PAYMENTS_MODULE_ENABLED:
        routes['endpoints']['payments'] = '/api/payments/'
    if settings.STAFF_MODULE_ENABLED:
        routes['endpoints']['staff'] = '/api/staff/'
    if settings.COMMS_MODULE_ENABLED:
        routes['endpoints']['comms'] = '/api/comms/'
    if settings.COMPLIANCE_MODULE_ENABLED:
        routes['endpoints']['compliance'] = '/api/compliance/'
    if settings.DOCUMENTS_MODULE_ENABLED:
        routes['endpoints']['documents'] = '/api/documents/'
    if settings.CRM_MODULE_ENABLED:
        routes['endpoints']['crm'] = '/api/crm/'
    if settings.ANALYTICS_MODULE_ENABLED:
        routes['endpoints']['analytics'] = '/api/analytics/'
    return JsonResponse(routes)


urlpatterns = [
    path('', api_index, name='api_index'),
    path('admin/', admin.site.urls),
    # Core auth endpoints (always enabled)
    path('api/auth/', include('accounts.urls')),
    # Audit log endpoints (always enabled)
    path('api/audit/', include('auditlog.urls')),
]

# Conditionally include module URLs based on feature flags
if settings.TENANTS_MODULE_ENABLED:
    urlpatterns.append(path('api/tenant/', include('tenants.urls')))
if settings.BOOKINGS_MODULE_ENABLED:
    urlpatterns.append(path('api/bookings/', include('bookings.urls')))
if settings.PAYMENTS_MODULE_ENABLED:
    urlpatterns.append(path('api/payments/', include('payments.urls')))
if settings.STAFF_MODULE_ENABLED:
    urlpatterns.append(path('api/staff/', include('staff.urls')))
if settings.COMMS_MODULE_ENABLED:
    urlpatterns.append(path('api/comms/', include('comms.urls')))
if settings.COMPLIANCE_MODULE_ENABLED:
    urlpatterns.append(path('api/compliance/', include('compliance.urls')))
if settings.DOCUMENTS_MODULE_ENABLED:
    urlpatterns.append(path('api/documents/', include('documents.urls')))
if settings.CRM_MODULE_ENABLED:
    urlpatterns.append(path('api/crm/', include('crm.urls')))
if settings.ANALYTICS_MODULE_ENABLED:
    urlpatterns.append(path('api/analytics/', include('analytics.urls')))

# Serve media files (uploads)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
