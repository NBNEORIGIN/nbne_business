from django.urls import path
from . import views

urlpatterns = [
    path('', views.tenant_settings, name='tenant_settings'),
    path('branding/', views.tenant_branding, name='tenant_branding'),
    path('update/', views.tenant_update, name='tenant_update'),
]
