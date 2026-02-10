from django.contrib import admin
from .models import Service, TimeSlot, Booking


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'duration_minutes', 'price_pence', 'deposit_pence', 'deposit_percentage', 'is_active', 'sort_order']
    list_filter = ['is_active', 'category']
    search_fields = ['name']


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['date', 'start_time', 'end_time', 'service', 'max_bookings', 'is_available']
    list_filter = ['is_available', 'date']
    date_hierarchy = 'date'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'customer_email', 'service', 'assigned_staff', 'status', 'price_pence', 'deposit_pence', 'created_at']
    list_filter = ['status', 'assigned_staff']
    search_fields = ['customer_name', 'customer_email']
    date_hierarchy = 'created_at'
