from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.document_list, name='document_list'),
    path('create/', views.document_create, name='document_create'),
    path('summary/', views.document_summary, name='document_summary'),
    path('categories/', views.document_categories, name='document_categories'),
    path('expiring/', views.expiry_reminders, name='expiry_reminders'),
    path('tags/', views.tag_list, name='tag_list'),
    path('tags/create/', views.tag_create, name='tag_create'),
    path('<int:doc_id>/', views.document_detail, name='document_detail'),
    path('<int:doc_id>/download/', views.document_download, name='document_download'),
    path('seed/', views.seed_vault, name='seed_vault'),
]
