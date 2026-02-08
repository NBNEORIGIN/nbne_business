from django.contrib import admin
from .models import Lead, LeadNote, FollowUp


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'source', 'status', 'value_pence', 'created_at']
    list_filter = ['status', 'source']
    search_fields = ['name', 'email']


@admin.register(LeadNote)
class LeadNoteAdmin(admin.ModelAdmin):
    list_display = ['lead', 'author', 'created_at']


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ['lead', 'assigned_to', 'due_date', 'is_completed']
    list_filter = ['is_completed']
