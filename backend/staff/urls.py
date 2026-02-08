from django.urls import path
from . import views

urlpatterns = [
    path('', views.staff_list, name='staff_list'),
    path('<int:staff_id>/', views.staff_detail, name='staff_detail'),
    path('my-shifts/', views.my_shifts, name='my_shifts'),
    path('shifts/', views.shift_list, name='shift_list'),
    path('shifts/create/', views.shift_create, name='shift_create'),
    path('leave/', views.leave_list, name='leave_list'),
    path('leave/create/', views.leave_create, name='leave_create'),
    path('leave/<int:leave_id>/review/', views.leave_review, name='leave_review'),
    path('training/', views.training_list, name='training_list'),
    path('training/create/', views.training_create, name='training_create'),
    path('absence/', views.absence_list, name='absence_list'),
    path('absence/create/', views.absence_create, name='absence_create'),
]
