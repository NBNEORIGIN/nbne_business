from django.urls import path
from . import views

urlpatterns = [
    path('', views.document_list, name='document_list'),
    path('create/', views.document_create, name='document_create'),
    path('<int:doc_id>/', views.document_detail, name='document_detail'),
    path('expiring/', views.expiry_reminders, name='expiry_reminders'),
    path('tags/', views.tag_list, name='tag_list'),
    path('tags/create/', views.tag_create, name='tag_create'),
]
