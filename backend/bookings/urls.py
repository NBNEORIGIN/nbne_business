from django.urls import path
from . import views

urlpatterns = [
    path('services/', views.service_list, name='service_list'),
    path('services/<int:service_id>/', views.service_detail, name='service_detail'),
    path('services/create/', views.service_create, name='service_create'),
    path('services/<int:service_id>/update/', views.service_update, name='service_update'),
    path('slots/', views.available_slots, name='available_slots'),
    path('create/', views.create_booking, name='create_booking'),
    path('', views.booking_list, name='booking_list'),
    path('<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('<int:booking_id>/delete/', views.delete_booking, name='delete_booking'),
    path('<int:booking_id>/confirm/', views.confirm_booking, name='confirm_booking'),
    path('<int:booking_id>/complete/', views.complete_booking, name='complete_booking'),
    path('<int:booking_id>/no-show/', views.mark_no_show, name='mark_no_show'),
    path('<int:booking_id>/assign-staff/', views.assign_staff, name='assign_staff'),
    path('staff-available/', views.bookable_staff, name='bookable_staff'),
    path('staff-slots/', views.staff_slots, name='staff_slots'),
    path('disclaimer/check/', views.disclaimer_check, name='disclaimer_check'),
    path('disclaimer/sign/', views.disclaimer_sign, name='disclaimer_sign'),
    path('disclaimer/void/', views.disclaimer_void, name='disclaimer_void'),
    path('lookup/', views.booking_lookup, name='booking_lookup'),
    path('reports/', views.booking_reports, name='booking_reports'),
    path('webhook/payment/', views.payment_webhook_callback, name='payment_webhook_callback'),
]
