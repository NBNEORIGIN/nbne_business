from django.urls import path
from . import views

urlpatterns = [
    path('channels/', views.channel_list, name='channel_list'),
    path('channels/create/', views.channel_create, name='channel_create'),
    path('channels/<int:channel_id>/', views.channel_detail, name='channel_detail'),
    path('channels/<int:channel_id>/messages/', views.message_list, name='message_list'),
    path('channels/<int:channel_id>/messages/create/', views.message_create, name='message_create'),
    path('push/subscribe/', views.push_subscribe, name='push_subscribe'),
    path('push/unsubscribe/', views.push_unsubscribe, name='push_unsubscribe'),
]
