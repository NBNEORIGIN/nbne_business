from rest_framework import serializers
from .models import IncidentReport, IncidentPhoto, SignOff, RAMSDocument


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
    photos = IncidentPhotoSerializer(many=True, read_only=True)
    sign_offs = SignOffSerializer(many=True, read_only=True)

    class Meta:
        model = IncidentReport
        fields = [
            'id', 'title', 'description', 'severity', 'status',
            'location', 'incident_date', 'reported_by_name', 'assigned_to_name',
            'resolution_notes', 'resolved_at', 'photos', 'sign_offs',
            'created_at', 'updated_at',
        ]

    def get_reported_by_name(self, obj):
        return obj.reported_by.get_full_name() if obj.reported_by else None

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.get_full_name() if obj.assigned_to else None


class IncidentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentReport
        fields = ['title', 'description', 'severity', 'location', 'incident_date', 'assigned_to']


class IncidentStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED'])
    resolution_notes = serializers.CharField(required=False, default='')


class SignOffCreateSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, default='')


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
