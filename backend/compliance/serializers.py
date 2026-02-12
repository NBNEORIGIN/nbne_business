from rest_framework import serializers
from .models import (
    ComplianceCategory, ComplianceItem, IncidentReport, IncidentPhoto,
    SignOff, TrainingRecord, DocumentVault, ComplianceActionLog, RAMSDocument,
)


# ---------------------------------------------------------------------------
# ComplianceCategory
# ---------------------------------------------------------------------------
class ComplianceCategorySerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()
    overdue_count = serializers.SerializerMethodField()

    class Meta:
        model = ComplianceCategory
        fields = ['id', 'name', 'description', 'legal_requirement', 'order', 'item_count', 'overdue_count']

    def get_item_count(self, obj):
        return obj.items.count()

    def get_overdue_count(self, obj):
        return obj.items.filter(status='overdue').count()


class ComplianceCategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceCategory
        fields = ['name', 'description', 'legal_requirement', 'order']


# ---------------------------------------------------------------------------
# ComplianceItem
# ---------------------------------------------------------------------------
class ComplianceItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    responsible_user_name = serializers.SerializerMethodField()
    legal_requirement = serializers.BooleanField(source='category.legal_requirement', read_only=True)

    class Meta:
        model = ComplianceItem
        fields = [
            'id', 'title', 'category', 'category_name', 'description',
            'frequency_type', 'frequency_days', 'last_completed_date',
            'next_due_date', 'responsible_user', 'responsible_user_name',
            'status', 'is_baseline', 'notes', 'legal_requirement',
            'created_at', 'updated_at',
        ]

    def get_responsible_user_name(self, obj):
        return obj.responsible_user.get_full_name() if obj.responsible_user else None


class ComplianceItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceItem
        fields = [
            'title', 'category', 'description', 'frequency_type',
            'frequency_days', 'last_completed_date', 'next_due_date',
            'responsible_user', 'notes',
        ]


class ComplianceItemCompleteSerializer(serializers.Serializer):
    completed_date = serializers.DateField(required=False)


# ---------------------------------------------------------------------------
# IncidentReport (with RIDDOR)
# ---------------------------------------------------------------------------
class IncidentPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentPhoto
        fields = ['id', 'image', 'caption', 'uploaded_at']


class SignOffSerializer(serializers.ModelSerializer):
    signed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = SignOff
        fields = ['id', 'signed_by_name', 'role', 'notes', 'signed_at']

    def get_signed_by_name(self, obj):
        return obj.signed_by.get_full_name() if obj.signed_by else 'Unknown'


class IncidentReportSerializer(serializers.ModelSerializer):
    reported_by_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()
    photos = IncidentPhotoSerializer(many=True, read_only=True)
    sign_offs = SignOffSerializer(many=True, read_only=True)

    class Meta:
        model = IncidentReport
        fields = [
            'id', 'title', 'description', 'severity', 'status',
            'location', 'incident_date', 'injury_type', 'riddor_reportable',
            'reported_by_name', 'assigned_to_name', 'reviewed_by_name',
            'resolution_notes', 'resolved_at', 'photos', 'sign_offs',
            'created_at', 'updated_at',
        ]

    def get_reported_by_name(self, obj):
        return obj.reported_by.get_full_name() if obj.reported_by else None

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.get_full_name() if obj.assigned_to else None

    def get_reviewed_by_name(self, obj):
        return obj.reviewed_by.get_full_name() if obj.reviewed_by else None


class IncidentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentReport
        fields = [
            'title', 'description', 'severity', 'location',
            'incident_date', 'injury_type', 'riddor_reportable', 'assigned_to',
        ]


class IncidentStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED'])
    resolution_notes = serializers.CharField(required=False, default='')


class SignOffCreateSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, default='')


# ---------------------------------------------------------------------------
# TrainingRecord
# ---------------------------------------------------------------------------
class TrainingRecordSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)

    class Meta:
        model = TrainingRecord
        fields = [
            'id', 'user', 'user_name', 'training_type', 'title', 'provider',
            'certificate_file', 'issue_date', 'expiry_date', 'status',
            'notes', 'created_at', 'updated_at',
        ]

    def get_user_name(self, obj):
        return obj.user.get_full_name() if obj.user else None


class TrainingRecordCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingRecord
        fields = [
            'user', 'training_type', 'title', 'provider',
            'certificate_file', 'issue_date', 'expiry_date', 'notes',
        ]


# ---------------------------------------------------------------------------
# DocumentVault
# ---------------------------------------------------------------------------
class DocumentVaultSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = DocumentVault
        fields = [
            'id', 'title', 'file', 'document_type', 'description',
            'expiry_date', 'version', 'is_current', 'is_expired',
            'uploaded_by_name', 'supersedes', 'created_at', 'updated_at',
        ]

    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() if obj.uploaded_by else None


class DocumentVaultCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentVault
        fields = ['title', 'file', 'document_type', 'description', 'expiry_date']


# ---------------------------------------------------------------------------
# ComplianceActionLog
# ---------------------------------------------------------------------------
class ComplianceActionLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()

    class Meta:
        model = ComplianceActionLog
        fields = ['id', 'action', 'user_name', 'target', 'notes', 'timestamp']

    def get_user_name(self, obj):
        return obj.user.get_full_name() if obj.user else 'System'

    def get_target(self, obj):
        if obj.compliance_item:
            return f"Item: {obj.compliance_item.title}"
        if obj.incident:
            return f"Incident: {obj.incident.title}"
        return 'General'


# ---------------------------------------------------------------------------
# RAMSDocument
# ---------------------------------------------------------------------------
class RAMSDocumentSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = RAMSDocument
        fields = [
            'id', 'title', 'reference_number', 'description', 'document',
            'status', 'issue_date', 'expiry_date', 'is_expired',
            'created_by_name', 'created_at', 'updated_at',
        ]

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None


class RAMSCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RAMSDocument
        fields = ['title', 'reference_number', 'description', 'document', 'status', 'issue_date', 'expiry_date']
