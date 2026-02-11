from datetime import timedelta as _timedelta
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class Service(models.Model):
    """A bookable service offered by the business."""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    category = models.CharField(max_length=100, blank=True, default='')
    duration_minutes = models.PositiveIntegerField(default=60)
    price_pence = models.PositiveIntegerField(default=0)
    deposit_pence = models.PositiveIntegerField(default=0)
    deposit_percentage = models.PositiveIntegerField(default=0, help_text='Default deposit as % of price (0=use deposit_pence instead)')
    colour = models.CharField(max_length=50, blank=True, default='')
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookings_service'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class TimeSlot(models.Model):
    """An available time window for bookings."""
    date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE,
        related_name='time_slots', null=True, blank=True,
    )
    max_bookings = models.PositiveIntegerField(default=1)
    is_available = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bookings_timeslot'
        ordering = ['date', 'start_time']
        indexes = [
            models.Index(fields=['date', 'start_time', 'is_available']),
        ]

    def __str__(self):
        svc = self.service.name if self.service else 'Any'
        return f"{self.date} {self.start_time}-{self.end_time} ({svc})"

    @property
    def current_booking_count(self):
        return self.bookings.exclude(status='CANCELLED').count()

    @property
    def has_capacity(self):
        return self.is_available and self.current_booking_count < self.max_bookings


class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PENDING_PAYMENT', 'Pending Payment'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('NO_SHOW', 'No Show'),
        ('CANCELLED', 'Cancelled'),
    ]

    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField(db_index=True)
    customer_phone = models.CharField(max_length=50, blank=True, default='')
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='bookings')
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.PROTECT, related_name='bookings', null=True, blank=True)
    booking_date = models.DateField(null=True, blank=True, db_index=True, help_text='Direct date for staff-aware bookings')
    booking_time = models.TimeField(null=True, blank=True, help_text='Direct start time for staff-aware bookings')
    assigned_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_bookings',
        help_text='Staff member assigned to this booking',
    )
    price_pence = models.PositiveIntegerField(default=0)
    deposit_pence = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    notes = models.TextField(blank=True, default='')
    cancellation_reason = models.TextField(blank=True, default='')
    payment_session_id = models.CharField(max_length=255, blank=True, default='', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookings_booking'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['customer_email']),
        ]

    def __str__(self):
        if self.time_slot:
            return f"{self.customer_name} — {self.service.name} @ {self.time_slot.date} {self.time_slot.start_time}"
        return f"{self.customer_name} — {self.service.name} @ {self.booking_date} {self.booking_time}"

    def clean(self):
        if self.time_slot_id and self.status != 'CANCELLED':
            existing = Booking.objects.filter(
                time_slot=self.time_slot
            ).exclude(status='CANCELLED').exclude(pk=self.pk)
            if existing.count() >= self.time_slot.max_bookings:
                raise ValidationError('This time slot is fully booked.')
        if not self.time_slot_id and not (self.booking_date and self.booking_time):
            raise ValidationError('Either time_slot or booking_date+booking_time is required.')

    def save(self, *args, **kwargs):
        if not kwargs.get('update_fields'):
            self.full_clean()
        super().save(*args, **kwargs)

    def cancel(self, reason=''):
        self.status = 'CANCELLED'
        self.cancellation_reason = reason
        self.save(update_fields=['status', 'cancellation_reason', 'updated_at'])

    def confirm(self):
        self.status = 'CONFIRMED'
        self.save(update_fields=['status', 'updated_at'])

    def complete(self):
        self.status = 'COMPLETED'
        self.save(update_fields=['status', 'updated_at'])

    def no_show(self):
        self.status = 'NO_SHOW'
        self.save(update_fields=['status', 'updated_at'])

    @property
    def deposit_percentage_actual(self):
        if self.price_pence and self.price_pence > 0:
            return round((self.deposit_pence / self.price_pence) * 100, 1)
        return 0


class DisclaimerTemplate(models.Model):
    """A disclaimer/waiver form that clients must sign before booking.
    Configurable per-business. When updated, existing signatures can be
    invalidated so clients must re-sign."""
    title = models.CharField(max_length=255, default='Terms & Conditions')
    body = models.TextField(help_text='Full disclaimer text shown to the client')
    is_active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1, help_text='Increment to require re-signing')
    validity_days = models.PositiveIntegerField(default=365, help_text='Days before signature expires (0=never)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookings_disclaimer_template'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} (v{self.version})"


class ClientDisclaimer(models.Model):
    """Record of a client signing a disclaimer. Linked by email.
    Expires after validity_days or when the template version changes."""
    customer_email = models.EmailField(db_index=True)
    customer_name = models.CharField(max_length=255)
    disclaimer = models.ForeignKey(DisclaimerTemplate, on_delete=models.CASCADE, related_name='signatures')
    version_signed = models.PositiveIntegerField()
    signed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_void = models.BooleanField(default=False, help_text='Admin can void to force re-signing')

    class Meta:
        db_table = 'bookings_client_disclaimer'
        ordering = ['-signed_at']
        indexes = [
            models.Index(fields=['customer_email', 'disclaimer']),
        ]

    def __str__(self):
        return f"{self.customer_email} signed {self.disclaimer.title} v{self.version_signed}"

    @property
    def is_valid(self):
        if self.is_void:
            return False
        if self.version_signed < self.disclaimer.version:
            return False
        if self.disclaimer.validity_days > 0:
            from django.utils import timezone as tz
            expiry = self.signed_at + _timedelta(days=self.disclaimer.validity_days)
            if tz.now() > expiry:
                return False
        return True
