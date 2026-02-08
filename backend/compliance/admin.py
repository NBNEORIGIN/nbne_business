from django.contrib import admin
from .models import IncidentReport, IncidentPhoto, SignOff, RAMSDocument


@admin.register(IncidentReport)
class IncidentReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'severity', 'status', 'location', 'incident_date', 'reported_by']
    list_filter = ['severity', 'status']
    search_fields = ['title', 'description']
    date_hierarchy = 'incident_date'


@admin.register(IncidentPhoto)
class IncidentPhotoAdmin(admin.ModelAdmin):
    list_display = ['incident', 'caption', 'uploaded_at']


@admin.register(SignOff)
class SignOffAdmin(admin.ModelAdmin):
    list_display = ['incident', 'signed_by', 'role', 'signed_at']


@admin.register(RAMSDocument)
class RAMSDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'reference_number', 'status', 'issue_date', 'expiry_date']
    list_filter = ['status']
    search_fields = ['title', 'reference_number']
