from rest_framework import serializers
from .models import Channel, Message, Attachment


class ChannelSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Channel
        fields = [
            'id', 'name', 'channel_type', 'description',
            'member_count', 'is_archived', 'created_by_name',
            'created_at', 'updated_at',
        ]

    def get_member_count(self, obj):
        return obj.members.count()

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None


class ChannelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ['name', 'channel_type', 'description']


class AttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = ['id', 'filename', 'content_type', 'size_bytes', 'url', 'uploaded_at']

    def get_url(self, obj):
        if obj.file:
            return obj.file.url
        return None


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    sender_id = serializers.IntegerField(source='sender.id', read_only=True, default=None)
    attachments = AttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'channel', 'sender_id', 'sender_name',
            'body', 'is_pinned', 'is_edited', 'parent',
            'attachments', 'created_at', 'updated_at',
        ]

    def get_sender_name(self, obj):
        return obj.sender.get_full_name() if obj.sender else 'System'


class MessageCreateSerializer(serializers.Serializer):
    body = serializers.CharField()
    parent = serializers.IntegerField(required=False, allow_null=True, default=None)
