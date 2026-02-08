from django.conf import settings
from django.db import models


class AuditEntry(models.Model):
    """Immutable audit trail entry for all significant actions."""

    ACTION_CHOICES = [
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('EXPORT', 'Export'),
        ('STATUS_CHANGE', 'Status Change'),
        ('ROLE_CHANGE', 'Role Change'),
        ('PASSWORD_CHANGE', 'Password Change'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='audit_entries',
    )
    user_name = models.CharField(max_length=150, default='')
    user_role = models.CharField(max_length=20, default='')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    entity_type = models.CharField(max_length=100, default='')
    entity_id = models.CharField(max_length=100, default='')
    details = models.TextField(blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Entry'
        verbose_name_plural = 'Audit Entries'

    def __str__(self):
        return f'{self.timestamp} | {self.user_name} | {self.action} | {self.entity_type}'

    @classmethod
    def log(cls, request, action, entity_type='', entity_id='', details=''):
        """Create an audit entry from a request context."""
        user = getattr(request, 'user', None)
        if user and not user.is_authenticated:
            user = None

        ip = cls._get_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT', '')[:500]

        return cls.objects.create(
            user=user,
            user_name=user.get_full_name() if user else 'Anonymous',
            user_role=getattr(user, 'role', '') if user else '',
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            details=details,
            ip_address=ip,
            user_agent=ua,
        )

    @staticmethod
    def _get_client_ip(request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
