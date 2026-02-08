from rest_framework import serializers
from .models import Document, DocumentTag


class DocumentTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentTag
        fields = ['id', 'name']


class DocumentSerializer(serializers.ModelSerializer):
    tags = DocumentTagSerializer(many=True, read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'category', 'file', 'file_size',
            'tier_access', 'tags', 'uploaded_by_name', 'expiry_date',
            'is_expired', 'is_active', 'created_at', 'updated_at',
        ]

    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() if obj.uploaded_by else None


class DocumentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['title', 'description', 'category', 'file', 'tier_access', 'expiry_date']
