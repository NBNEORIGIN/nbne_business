from django.contrib import admin
from .models import AuditEntry


@admin.register(AuditEntry)
class AuditEntryAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user_name', 'user_role', 'action', 'entity_type', 'entity_id', 'ip_address']
    list_filter = ['action', 'user_role', 'entity_type']
    search_fields = ['user_name', 'entity_type', 'details']
    readonly_fields = [f.name for f in AuditEntry._meta.fields]
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
