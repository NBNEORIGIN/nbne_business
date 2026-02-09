from django.urls import path
from . import views

urlpatterns = [
    path('', views.staff_list, name='staff_list'),
    path('create/', views.staff_create, name='staff_create'),
    path('<int:staff_id>/', views.staff_detail, name='staff_detail'),
    path('<int:staff_id>/update/', views.staff_update, name='staff_update'),
    path('<int:staff_id>/delete/', views.staff_delete, name='staff_delete'),
    path('my-shifts/', views.my_shifts, name='my_shifts'),
    path('shifts/', views.shift_list, name='shift_list'),
    path('shifts/create/', views.shift_create, name='shift_create'),
    path('shifts/<int:shift_id>/update/', views.shift_update, name='shift_update'),
    path('shifts/<int:shift_id>/delete/', views.shift_delete, name='shift_delete'),
    path('leave/', views.leave_list, name='leave_list'),
    path('leave/create/', views.leave_create, name='leave_create'),
    path('leave/<int:leave_id>/review/', views.leave_review, name='leave_review'),
    path('training/', views.training_list, name='training_list'),
    path('training/create/', views.training_create, name='training_create'),
    path('absence/', views.absence_list, name='absence_list'),
    path('absence/create/', views.absence_create, name='absence_create'),
    # Working Hours
    path('working-hours/', views.working_hours_list, name='working_hours_list'),
    path('working-hours/create/', views.working_hours_create, name='working_hours_create'),
    path('working-hours/<int:wh_id>/update/', views.working_hours_update, name='working_hours_update'),
    path('working-hours/<int:wh_id>/delete/', views.working_hours_delete, name='working_hours_delete'),
    path('working-hours/bulk-set/', views.working_hours_bulk_set, name='working_hours_bulk_set'),
    # Timesheets
    path('timesheets/', views.timesheet_list, name='timesheet_list'),
    path('timesheets/<int:ts_id>/update/', views.timesheet_update, name='timesheet_update'),
    path('timesheets/generate/', views.timesheet_generate, name='timesheet_generate'),
    path('timesheets/summary/', views.timesheet_summary, name='timesheet_summary'),
]
