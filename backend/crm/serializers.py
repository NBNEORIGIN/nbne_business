from rest_framework import serializers
from .models import Lead, LeadNote, FollowUp


class LeadNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = LeadNote
        fields = ['id', 'author_name', 'body', 'created_at']

    def get_author_name(self, obj):
        return obj.author.get_full_name() if obj.author else None


class FollowUpSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = FollowUp
        fields = ['id', 'assigned_to_name', 'due_date', 'description', 'is_completed', 'completed_at', 'created_at']

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.get_full_name() if obj.assigned_to else None


class LeadSerializer(serializers.ModelSerializer):
    lead_notes = LeadNoteSerializer(many=True, read_only=True)
    follow_ups = FollowUpSerializer(many=True, read_only=True)
    assigned_to_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = [
            'id', 'name', 'email', 'phone', 'source', 'status',
            'value_pence', 'notes', 'assigned_to_name', 'created_by_name',
            'lead_notes', 'follow_ups', 'created_at', 'updated_at',
        ]

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.get_full_name() if obj.assigned_to else None

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None


class LeadCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ['name', 'email', 'phone', 'source', 'value_pence', 'notes', 'assigned_to']


class LeadStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['NEW', 'CONTACTED', 'QUALIFIED', 'CONVERTED', 'LOST'])


class NoteCreateSerializer(serializers.Serializer):
    body = serializers.CharField()


class FollowUpCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowUp
        fields = ['due_date', 'description', 'assigned_to']
