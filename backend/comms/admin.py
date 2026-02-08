from django.contrib import admin
from .models import Channel, Message, Attachment, PushSubscription


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'channel_type', 'is_archived', 'created_at']
    list_filter = ['channel_type', 'is_archived']
    search_fields = ['name']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'channel', 'sender', 'body_preview', 'is_pinned', 'created_at']
    list_filter = ['is_pinned']
    search_fields = ['body']

    def body_preview(self, obj):
        return obj.body[:80]


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'message', 'content_type', 'size_bytes']


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_active', 'created_at']
