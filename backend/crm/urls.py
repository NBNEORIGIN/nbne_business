from django.urls import path
from . import views

urlpatterns = [
    path('leads/', views.lead_list, name='lead_list'),
    path('leads/create/', views.lead_create, name='lead_create'),
    path('leads/export/', views.lead_export_csv, name='lead_export_csv'),
    path('leads/<int:lead_id>/', views.lead_detail, name='lead_detail'),
    path('leads/<int:lead_id>/status/', views.lead_update_status, name='lead_update_status'),
    path('leads/<int:lead_id>/notes/create/', views.note_create, name='note_create'),
    path('leads/<int:lead_id>/follow-ups/create/', views.follow_up_create, name='follow_up_create'),
    path('follow-ups/<int:follow_up_id>/complete/', views.follow_up_complete, name='follow_up_complete'),
]
