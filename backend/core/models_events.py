"""
BusinessEvent — Immutable event log for all dashboard actions.

Every dashboard action generates a BusinessEvent. No silent state mutation.
Dashboard state is derived from events, not from mutable flags.

Events auto-expire from the Sorted view after 24 hours but remain
permanently in the audit log.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class BusinessEvent(models.Model):
    """Immutable record of an operational event or action taken."""

    EVENT_TYPES = [
        # Operational
        ('STAFF_SICK', 'Staff Sick'),
        ('COVER_REQUESTED', 'Cover Requested'),
        ('COVER_ACCEPTED', 'Cover Accepted'),
        ('COVER_DECLINED', 'Cover Declined'),
        # Bookings
        ('BOOKING_ASSIGNED', 'Booking Assigned'),
        ('BOOKING_CANCELLED', 'Booking Cancelled'),
        ('BOOKING_RESCHEDULED', 'Booking Rescheduled'),
        # Payments
        ('PAYMENT_REQUESTED', 'Payment Requested'),
        ('PAYMENT_MARKED', 'Payment Marked'),
        # Compliance
        ('COMPLIANCE_COMPLETED', 'Compliance Completed'),
        ('INCIDENT_RESOLVED', 'Incident Resolved'),
        # Leave
        ('LEAVE_APPROVED', 'Leave Approved'),
        ('LEAVE_DECLINED', 'Leave Declined'),
        # Owner
        ('OWNER_OVERRIDE', 'Owner Override'),
        # Assistant
        ('ASSISTANT_COMMAND', 'Assistant Command'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, null=True, blank=True, related_name='business_events')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='COMPLETED')

    # What triggered this event (the dashboard issue)
    source_event_type = models.CharField(
        max_length=50, blank=True, default='',
        help_text='The operational event type that triggered this action (e.g. staff_sick)',
    )
    source_entity_type = models.CharField(max_length=50, blank=True, default='')
    source_entity_id = models.IntegerField(null=True, blank=True)

    # What action was taken
    action_label = models.CharField(
        max_length=255,
        help_text='The action label clicked by the owner (e.g. "Ask Jordan to cover")',
    )
    action_detail = models.TextField(
        blank=True, default='',
        help_text='Additional context about the action taken',
    )

    # Who did it
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='business_events',
    )

    # Structured payload for machine consumption
    payload = models.JSONField(
        default=dict, blank=True,
        help_text='Structured data: entities, parameters, assistant parse result, etc.',
    )

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['source_entity_type', 'source_entity_id']),
        ]
        verbose_name = 'Business Event'
        verbose_name_plural = 'Business Events'

    def __str__(self):
        return f'{self.get_event_type_display()} — {self.action_label} ({self.created_at:%H:%M})'

    @classmethod
    def log(cls, event_type, action_label, user=None, source_event_type='',
            source_entity_type='', source_entity_id=None, action_detail='',
            payload=None, status='COMPLETED', tenant=None):
        """Convenience factory for creating events."""
        return cls.objects.create(
            tenant=tenant,
            event_type=event_type,
            status=status,
            source_event_type=source_event_type,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            action_label=action_label,
            action_detail=action_detail,
            performed_by=user,
            payload=payload or {},
        )

    @classmethod
    def today_resolved(cls, tenant=None):
        """Return events from today that represent resolved dashboard actions."""
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        qs = cls.objects.filter(
            created_at__gte=today_start,
            status='COMPLETED',
        )
        if tenant:
            qs = qs.filter(tenant=tenant)
        return qs.select_related('performed_by')
