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
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.PROTECT, related_name='bookings')
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
        return f"{self.customer_name} — {self.service.name} @ {self.time_slot.date} {self.time_slot.start_time}"

    def clean(self):
        if self.time_slot_id and self.status != 'CANCELLED':
            existing = Booking.objects.filter(
                time_slot=self.time_slot
            ).exclude(status='CANCELLED').exclude(pk=self.pk)
            if existing.count() >= self.time_slot.max_bookings:
                raise ValidationError('This time slot is fully booked.')

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
