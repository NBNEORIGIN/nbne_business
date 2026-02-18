from django.urls import path
from . import views

app_name = 'compliance'

urlpatterns = [
    # Dashboard & scoring
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard-v2/', views.dashboard_v2, name='dashboard-v2'),
    path('wiggum/', views.wiggum, name='wiggum'),
    path('parse-command/', views.parse_command, name='parse-command'),
    path('breakdown/', views.breakdown, name='breakdown'),
    path('priorities/', views.priority_actions, name='priorities'),
    path('audit-log/', views.audit_log, name='audit-log'),
    path('recalculate/', views.recalculate, name='recalculate'),
    path('categories/', views.categories_list, name='categories'),
    # Compliance register CRUD
    path('items/', views.items_list, name='items-list'),
    path('items/create/', views.items_create, name='items-create'),
    path('items/<int:item_id>/', views.items_detail, name='items-detail'),
    path('items/<int:item_id>/complete/', views.mark_complete, name='mark-complete'),
    path('items/<int:item_id>/delete/', views.items_delete, name='items-delete'),
    # Calendar
    path('calendar/', views.calendar_data, name='calendar'),
    # Accident log
    path('accidents/', views.accidents_list, name='accidents-list'),
    path('accidents/create/', views.accidents_create, name='accidents-create'),
    path('accidents/<int:accident_id>/update/', views.accidents_update, name='accidents-update'),
    path('accidents/<int:accident_id>/delete/', views.accidents_delete, name='accidents-delete'),
    # Incidents
    path('incidents/', views.incidents_list, name='incidents-list'),
    path('incidents/create/', views.incidents_create, name='incidents-create'),
    path('incidents/<int:incident_id>/status/', views.incidents_status, name='incidents-status'),
    # RAMS & Documents
    path('rams/', views.rams_list, name='rams-list'),
    path('documents/', views.compliance_documents_list, name='compliance-documents'),
]
