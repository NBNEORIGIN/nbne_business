from django.contrib import admin
from .models import Service, TimeSlot, Booking, DisclaimerTemplate, ClientDisclaimer


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


@admin.register(DisclaimerTemplate)
class DisclaimerTemplateAdmin(admin.ModelAdmin):
    list_display = ['title', 'version', 'is_active', 'validity_days', 'updated_at']
    list_filter = ['is_active']


@admin.register(ClientDisclaimer)
class ClientDisclaimerAdmin(admin.ModelAdmin):
    list_display = ['customer_email', 'customer_name', 'disclaimer', 'version_signed', 'signed_at', 'is_void']
    list_filter = ['is_void', 'disclaimer']
    search_fields = ['customer_email', 'customer_name']
    date_hierarchy = 'signed_at'
