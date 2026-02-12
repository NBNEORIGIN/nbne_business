from django.urls import path
from . import views

urlpatterns = [
    # --- Tier 3: Dashboard & Calendar ---
    path('dashboard/', views.compliance_dashboard, name='compliance_dashboard'),
    path('calendar/', views.calendar_feed, name='calendar_feed'),
    path('export/', views.export_csv, name='export_csv'),

    # --- Tier 3: Categories CRUD ---
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:category_id>/', views.category_detail, name='category_detail'),

    # --- Tier 3: Items CRUD ---
    path('items/', views.item_list, name='item_list'),
    path('items/create/', views.item_create, name='item_create'),
    path('items/<int:item_id>/', views.item_detail, name='item_detail'),
    path('items/<int:item_id>/complete/', views.item_complete, name='item_complete'),
    path('items/<int:item_id>/assign/', views.item_assign, name='item_assign'),

    # --- Tier 2: My Actions & Training ---
    path('my-actions/', views.my_actions, name='my_actions'),
    path('my-training/', views.my_training, name='my_training'),

    # --- Tier 3: Training CRUD ---
    path('training/', views.training_list, name='training_list'),
    path('training/create/', views.training_create, name='training_create'),
    path('training/<int:training_id>/', views.training_detail, name='training_detail'),

    # --- Tier 3: Document Vault ---
    path('documents/', views.document_list, name='document_list'),
    path('documents/upload/', views.document_upload, name='document_upload'),
    path('documents/<int:doc_id>/', views.document_detail, name='document_detail'),
    path('documents/<int:doc_id>/new-version/', views.document_new_version, name='document_new_version'),
    path('documents/<int:doc_id>/versions/', views.document_versions, name='document_versions'),

    # --- Tier 3: Action Logs ---
    path('logs/', views.action_log_list, name='action_log_list'),

    # --- Tier 2: Incidents ---
    path('incidents/', views.incident_list, name='incident_list'),
    path('incidents/create/', views.incident_create, name='incident_create'),
    path('incidents/<int:incident_id>/', views.incident_detail, name='incident_detail'),
    path('incidents/<int:incident_id>/photo/', views.incident_upload_photo, name='incident_upload_photo'),
    path('incidents/<int:incident_id>/status/', views.incident_update_status, name='incident_update_status'),
    path('incidents/<int:incident_id>/sign-off/', views.incident_sign_off, name='incident_sign_off'),

    # --- Tier 2+: RAMS ---
    path('rams/', views.rams_list, name='rams_list'),
    path('rams/create/', views.rams_create, name='rams_create'),
    path('rams/<int:rams_id>/', views.rams_detail, name='rams_detail'),
]
