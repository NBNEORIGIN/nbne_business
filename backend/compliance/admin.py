from django.contrib import admin
from .models import (
    ComplianceCategory, ComplianceItem, IncidentReport, IncidentPhoto,
    SignOff, TrainingRecord, DocumentVault, ComplianceActionLog, RAMSDocument,
)


# --- Inlines ---
class ComplianceItemInline(admin.TabularInline):
    model = ComplianceItem
    extra = 0
    fields = ['title', 'frequency_type', 'status', 'next_due_date', 'responsible_user']


class IncidentPhotoInline(admin.TabularInline):
    model = IncidentPhoto
    extra = 0


class SignOffInline(admin.TabularInline):
    model = SignOff
    extra = 0
    readonly_fields = ['signed_at']


# --- ComplianceCategory ---
@admin.register(ComplianceCategory)
class ComplianceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'legal_requirement', 'order', 'item_count']
    list_filter = ['legal_requirement']
    search_fields = ['name']
    inlines = [ComplianceItemInline]

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'


# --- ComplianceItem ---
@admin.register(ComplianceItem)
class ComplianceItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'frequency_type', 'status', 'next_due_date', 'responsible_user', 'is_baseline']
    list_filter = ['status', 'frequency_type', 'category', 'is_baseline']
    search_fields = ['title', 'description']
    list_editable = ['status']
    date_hierarchy = 'next_due_date'
    actions = ['mark_compliant', 'run_status_update']

    def mark_compliant(self, request, queryset):
        for item in queryset:
            item.mark_completed()
        self.message_user(request, f'{queryset.count()} item(s) marked completed.')
    mark_compliant.short_description = 'Mark selected as completed (recalculate due date)'

    def run_status_update(self, request, queryset):
        updated = 0
        for item in queryset:
            old = item.status
            item.update_status()
            if item.status != old:
                item.save(update_fields=['status'])
                updated += 1
        self.message_user(request, f'{updated} item(s) status updated.')
    run_status_update.short_description = 'Recalculate status based on due dates'


# --- IncidentReport ---
@admin.register(IncidentReport)
class IncidentReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'severity', 'status', 'location', 'incident_date', 'injury_type', 'riddor_reportable', 'reported_by']
    list_filter = ['severity', 'status', 'riddor_reportable', 'injury_type']
    search_fields = ['title', 'description']
    date_hierarchy = 'incident_date'
    inlines = [IncidentPhotoInline, SignOffInline]


# --- TrainingRecord ---
@admin.register(TrainingRecord)
class TrainingRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'training_type', 'issue_date', 'expiry_date', 'status_display']
    list_filter = ['training_type']
    search_fields = ['user__first_name', 'user__last_name', 'title']
    date_hierarchy = 'expiry_date'

    def status_display(self, obj):
        s = obj.status
        if s == 'expired':
            return '❌ Expired'
        if s == 'expiring_soon':
            return '⚠️ Expiring Soon'
        return '✅ Valid'
    status_display.short_description = 'Status'


# --- DocumentVault ---
@admin.register(DocumentVault)
class DocumentVaultAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'version', 'is_current', 'expiry_date', 'uploaded_by']
    list_filter = ['document_type', 'is_current']
    search_fields = ['title', 'description']


# --- ComplianceActionLog ---
@admin.register(ComplianceActionLog)
class ComplianceActionLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'action', 'user', 'target_display', 'notes']
    list_filter = ['action']
    readonly_fields = ['timestamp', 'action', 'user', 'compliance_item', 'incident', 'notes']
    date_hierarchy = 'timestamp'

    def target_display(self, obj):
        if obj.compliance_item:
            return f"Item: {obj.compliance_item.title}"
        if obj.incident:
            return f"Incident: {obj.incident.title}"
        return '—'
    target_display.short_description = 'Target'

    def has_add_permission(self, request):
        return False


# --- RAMSDocument ---
@admin.register(RAMSDocument)
class RAMSDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'reference_number', 'status', 'issue_date', 'expiry_date']
    list_filter = ['status']
    search_fields = ['title', 'reference_number']
