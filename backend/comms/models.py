from django.conf import settings
from django.db import models


class Channel(models.Model):
    TYPE_CHOICES = [
        ('GENERAL', 'General'), ('TEAM', 'Team'), ('SHIFT', 'Shift'),
        ('JOB', 'Job'), ('INCIDENT', 'Incident'), ('DIRECT', 'Direct Message'),
    ]

    name = models.CharField(max_length=255)
    channel_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='GENERAL', db_index=True)
    description = models.TextField(blank=True, default='')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chat_channels', blank=True)
    is_archived = models.BooleanField(default=False, db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_channels')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comms_channel'
        ordering = ['-updated_at']

    def __str__(self):
        return f"#{self.name} ({self.get_channel_type_display()})"


class Message(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    body = models.TextField()
    is_pinned = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comms_message'
        ordering = ['created_at']

    def __str__(self):
        sender_name = self.sender.get_full_name() if self.sender else 'System'
        return f"{sender_name}: {self.body[:50]}"


class Attachment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='comms/attachments/%Y/%m/')
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, blank=True, default='')
    size_bytes = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comms_attachment'

    def __str__(self):
        return self.filename


class PushSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.URLField(max_length=500)
    p256dh_key = models.CharField(max_length=255)
    auth_key = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comms_push_subscription'
        unique_together = ['user', 'endpoint']

    def __str__(self):
        return f"{self.user.username} — {self.endpoint[:50]}"
