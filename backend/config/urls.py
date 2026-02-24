"""
URL configuration for NBNE Business Platform (Rev 3).
Conditionally includes module URLs based on feature flags in settings.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.http import FileResponse, Http404, JsonResponse
import os

from core.auth_views import (
    login_view, me_view, set_password_view,
    request_password_reset_view, validate_token_view,
    set_password_with_token_view, send_invite_view,
)
from core.views_dashboard_v2 import dashboard_today
from core.views_events import log_event, today_resolved, decline_cover
from core.views_assistant import parse_command
from core.command_router import execute_command, command_suggestions
from core.views_contact import contact_form
from core.views_beta import beta_signup
from core.views_feedback import feedback_submit
from core.views_ai_assistant import ai_chat


def api_index(request):
    """Root endpoint listing all available API routes."""
    routes = {
        'api': 'NBNE Business Platform',
        'version': '3.0.0',
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
    return JsonResponse(routes)


# --- Core URL patterns (always enabled) ---
urlpatterns = [
    path('', api_index, name='api_index'),
    path('admin/', admin.site.urls),
    # JWT Auth (core)
    path('api/auth/login/', login_view, name='auth-login'),
    path('api/auth/me/', me_view, name='auth-me'),
    path('api/auth/me/set-password/', set_password_view, name='auth-set-password'),
    path('api/auth/password-reset/', request_password_reset_view, name='auth-password-reset'),
    path('api/auth/validate-token/', validate_token_view, name='auth-validate-token'),
    path('api/auth/set-password-token/', set_password_with_token_view, name='auth-set-password-token'),
    path('api/auth/invite/', send_invite_view, name='auth-invite'),
    # Accounts (rev_2 auth — always enabled)
    path('api/auth/accounts/', include('accounts.urls')),
    # Audit log (always enabled)
    path('api/audit/', include('auditlog.urls')),
    # Core API (config, health, etc.)
    path('api/', include('core.api_urls')),
    # Tenant/branding alias (frontend expects /api/tenant/branding/)
    path('api/tenant/branding/', include('core.api_urls_branding')),
    path('api/tenant/', include('core.api_urls_tenant')),
    # Dashboard v2 — operational incident board (flag checked inside view)
    path('api/dashboard/today/', dashboard_today, name='dashboard-today'),
    # Business events — event logging discipline
    path('api/events/log/', log_event, name='event-log'),
    path('api/events/today/', today_resolved, name='events-today'),
    path('api/events/decline/', decline_cover, name='events-decline'),
    # Assistant — stateless command parser
    path('api/assistant/parse/', parse_command, name='assistant-parse'),
    # Global command bar
    path('api/command/', execute_command, name='command-execute'),
    path('api/command/suggestions/', command_suggestions, name='command-suggestions'),
    # AI assistant chat panel
    path('api/assistant/chat/', ai_chat, name='ai-chat'),
    # Public contact form (no auth required)
    path('api/contact/', contact_form, name='contact-form'),
    # Public beta signup form (no auth required)
    path('api/beta-signup/', beta_signup, name='beta-signup'),
    # Authenticated feedback from admin panel
    path('api/feedback/', feedback_submit, name='feedback-submit'),
    # Core catch-all (health check etc.)
    path('', include('core.urls')),
]

# --- Bookings module ---
if settings.BOOKINGS_MODULE_ENABLED:
    from rest_framework.routers import DefaultRouter
    from bookings.api_views import ServiceViewSet, StaffViewSet, BookingViewSet, ClientViewSet, StaffBlockViewSet, SessionViewSet
    from bookings.views_schedule import BusinessHoursViewSet, StaffScheduleViewSet, ClosureViewSet, StaffLeaveViewSet
    from bookings.views_intake import IntakeProfileViewSet, IntakeWellbeingDisclaimerViewSet
    from bookings.views_payment import ClassPackageViewSet, ClientCreditViewSet, PaymentIntegrationViewSet
    from bookings.views_stripe import create_checkout_session, stripe_webhook
    from bookings.views_dashboard import dashboard_summary, backfill_sbe
    from bookings.views_working_hours import working_hours_list, working_hours_bulk_set, working_hours_delete
    from bookings.views_timesheets import timesheets_list, timesheets_update, timesheets_generate, timesheets_summary
    from bookings.views_reports import (
        reports_overview, reports_daily, reports_monthly, reports_staff,
        reports_insights, reports_staff_hours, reports_staff_hours_csv, reports_leave,
    )
    from bookings.views_restaurant import TableViewSet, ServiceWindowViewSet, restaurant_availability, restaurant_available_dates
    from bookings.views_gym import ClassTypeViewSet, ClassSessionViewSet, gym_timetable, gym_class_types
    from bookings.views_demo import demo_seed_view, demo_status_view
    from bookings.views_demo_availability import demo_availability_seed_view
    from bookings.views_availability import (
        WorkingPatternViewSet, WorkingPatternRuleViewSet,
        AvailabilityOverrideViewSet, LeaveRequestViewSet,
        BlockedTimeViewSet, ShiftViewSet, TimesheetEntryViewSet,
        staff_availability_view, staff_free_slots_view,
    )

    router = DefaultRouter()
    router.register(r'services', ServiceViewSet, basename='service')
    router.register(r'staff', StaffViewSet, basename='staff')
    router.register(r'bookings', BookingViewSet, basename='booking')
    router.register(r'clients', ClientViewSet, basename='client')
    router.register(r'staff-blocks', StaffBlockViewSet, basename='staff-block')
    router.register(r'business-hours', BusinessHoursViewSet)
    router.register(r'staff-schedules', StaffScheduleViewSet)
    router.register(r'closures', ClosureViewSet)
    router.register(r'staff-leave', StaffLeaveViewSet)
    router.register(r'intake', IntakeProfileViewSet)
    router.register(r'intake-disclaimer', IntakeWellbeingDisclaimerViewSet)
    router.register(r'packages', ClassPackageViewSet)
    router.register(r'credits', ClientCreditViewSet)
    router.register(r'payment', PaymentIntegrationViewSet, basename='payment')
    router.register(r'sessions', SessionViewSet, basename='session')
    # Restaurant
    router.register(r'tables', TableViewSet, basename='table')
    router.register(r'service-windows', ServiceWindowViewSet, basename='service-window')
    # Gym
    router.register(r'class-types', ClassTypeViewSet, basename='class-type')
    router.register(r'class-sessions', ClassSessionViewSet, basename='class-session')
    # Availability engine
    router.register(r'working-patterns', WorkingPatternViewSet, basename='working-pattern')
    router.register(r'working-pattern-rules', WorkingPatternRuleViewSet, basename='working-pattern-rule')
    router.register(r'availability-overrides', AvailabilityOverrideViewSet, basename='availability-override')
    router.register(r'leave-requests', LeaveRequestViewSet, basename='leave-request')
    router.register(r'blocked-times', BlockedTimeViewSet, basename='blocked-time')
    router.register(r'shifts', ShiftViewSet, basename='shift')
    router.register(r'timesheets', TimesheetEntryViewSet, basename='timesheet')

    urlpatterns += [
        # Working hours (must be before DRF router)
        path('api/staff/working-hours/', working_hours_list, name='working-hours-list'),
        path('api/staff/working-hours/bulk-set/', working_hours_bulk_set, name='working-hours-bulk-set'),
        path('api/staff/working-hours/<int:pk>/delete/', working_hours_delete, name='working-hours-delete'),
        # Timesheets (must be before DRF router)
        path('api/staff/timesheets/', timesheets_list, name='timesheets-list'),
        path('api/staff/timesheets/generate/', timesheets_generate, name='timesheets-generate'),
        path('api/staff/timesheets/summary/', timesheets_summary, name='timesheets-summary'),
        path('api/staff/timesheets/<int:pk>/update/', timesheets_update, name='timesheets-update'),
        # Restaurant & Gym public endpoints
        path('api/restaurant-availability/', restaurant_availability, name='restaurant-availability'),
        path('api/restaurant-available-dates/', restaurant_available_dates, name='restaurant-available-dates'),
        path('api/gym-timetable/', gym_timetable, name='gym-timetable'),
        path('api/gym-class-types/', gym_class_types, name='gym-class-types'),
        # Aliases for frontend compatibility
        path('api/bookings/staff-slots/', BookingViewSet.as_view({'get': 'slots'}), name='booking-staff-slots-alias'),
        path('api/bookings/create/', BookingViewSet.as_view({'post': 'create'}), name='booking-create-alias'),
        # DRF router (bookings, services, staff, etc.)
        path('api/', include(router.urls)),
        # Stripe checkout
        path('api/checkout/create/', create_checkout_session, name='checkout-create'),
        path('api/checkout/webhook/', stripe_webhook, name='stripe-webhook'),
        # Dashboard & reports
        path('api/dashboard-summary/', dashboard_summary, name='dashboard-summary'),
        path('api/backfill-sbe/', backfill_sbe, name='backfill-sbe'),
        path('api/reports/overview/', reports_overview, name='reports-overview'),
        path('api/reports/daily/', reports_daily, name='reports-daily'),
        path('api/reports/monthly/', reports_monthly, name='reports-monthly'),
        path('api/reports/staff/', reports_staff, name='reports-staff'),
        path('api/reports/insights/', reports_insights, name='reports-insights'),
        path('api/reports/staff-hours/', reports_staff_hours, name='reports-staff-hours'),
        path('api/reports/staff-hours/csv/', reports_staff_hours_csv, name='reports-staff-hours-csv'),
        path('api/reports/leave/', reports_leave, name='reports-leave'),
        # Demo data
        path('api/demo/seed/', demo_seed_view, name='demo-seed'),
        path('api/demo/status/', demo_status_view, name='demo-status'),
        path('api/demo/availability/seed/', demo_availability_seed_view, name='demo-availability-seed'),
        # Availability engine
        path('api/availability/', staff_availability_view, name='staff-availability'),
        path('api/availability/slots/', staff_free_slots_view, name='staff-free-slots'),
    ]

# --- Conditionally include module URLs ---
if settings.TENANTS_MODULE_ENABLED:
    urlpatterns.append(path('api/tenants/', include('tenants.urls')))
if settings.PAYMENTS_MODULE_ENABLED:
    urlpatterns.append(path('api/payments/', include('payments.urls')))
if settings.STAFF_MODULE_ENABLED:
    urlpatterns.append(path('api/staff-module/', include('staff.urls')))
if settings.COMMS_MODULE_ENABLED:
    urlpatterns.append(path('api/comms/', include('comms.urls')))
if settings.COMPLIANCE_MODULE_ENABLED:
    urlpatterns.append(path('api/compliance/', include('compliance.urls')))
if settings.DOCUMENTS_MODULE_ENABLED:
    urlpatterns.append(path('api/documents/', include('documents.urls')))
if settings.CRM_MODULE_ENABLED:
    urlpatterns.append(path('api/crm/', include('crm.urls')))


# --- Media file serving ---
def serve_media(request, path):
    """Serve uploaded media files in all environments (static() only works with DEBUG=True)."""
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.isfile(file_path):
        return FileResponse(open(file_path, 'rb'))
    raise Http404('File not found')

urlpatterns += [
    path('media/<path:path>', serve_media, name='serve-media'),
]
