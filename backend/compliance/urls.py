from django.urls import path
from . import views

urlpatterns = [
    path('incidents/', views.incident_list, name='incident_list'),
    path('incidents/create/', views.incident_create, name='incident_create'),
    path('incidents/<int:incident_id>/', views.incident_detail, name='incident_detail'),
    path('incidents/<int:incident_id>/status/', views.incident_update_status, name='incident_update_status'),
    path('incidents/<int:incident_id>/sign-off/', views.incident_sign_off, name='incident_sign_off'),
    path('rams/', views.rams_list, name='rams_list'),
    path('rams/create/', views.rams_create, name='rams_create'),
    path('rams/<int:rams_id>/', views.rams_detail, name='rams_detail'),
]
