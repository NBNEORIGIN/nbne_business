import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, EmailValidator
from django.utils import timezone
import threading

DATA_ORIGIN_CHOICES = [
    ('REAL', 'Real'),
    ('DEMO', 'Demo'),
]

# Import intake models
from .models_intake import IntakeProfile, IntakeWellbeingDisclaimer

# Import payment models
from .models_payment import ClassPackage, ClientCredit, PaymentTransaction

# Import availability engine models
from .models_availability import (
    WorkingPattern, WorkingPatternRule,
    AvailabilityOverride, AvailabilityOverridePeriod,
    LeaveRequest, BlockedTime, Shift, TimesheetEntry,
)

# Import restaurant models
from .models_restaurant import Table, ServiceWindow

class Service(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('full', 'Full Payment'),
        ('deposit', 'Deposit Required'),
        ('free', 'Free / No Payment'),
    ]

    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True, default='', help_text='e.g. Mindfulness, Group, Corporate')
    duration_minutes = models.IntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='full')
    deposit_pence = models.IntegerField(default=0, help_text='Fixed deposit amount in pence')
    deposit_percentage = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text='Deposit as percentage of price')
    colour = models.CharField(max_length=7, blank=True, default='', help_text='Hex colour for calendar display')
    sort_order = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    # Smart Booking Engine — demand intelligence
    demand_index = models.FloatField(default=0, help_text='Normalised 0-100 demand score')
    peak_time_multiplier = models.FloatField(default=1.0)
    off_peak_discount_allowed = models.BooleanField(default=True)
    no_show_adjustment_enabled = models.BooleanField(default=True)
    # Service Intelligence Layer (Phase 1)
    avg_booking_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_bookings = models.IntegerField(default=0)
    no_show_rate = models.FloatField(default=0, help_text='Percentage 0-100')
    avg_risk_score = models.FloatField(default=0)
    peak_utilisation_rate = models.FloatField(default=0, help_text='Percentage 0-100')
    off_peak_utilisation_rate = models.FloatField(default=0, help_text='Percentage 0-100')
    recommended_base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    recommended_deposit_percent = models.FloatField(null=True, blank=True)
    recommended_payment_type = models.CharField(max_length=30, blank=True, default='')
    price_elasticity_index = models.FloatField(default=0, help_text='0-100 sensitivity score')
    recommendation_reason = models.TextField(blank=True, default='')
    recommendation_confidence = models.FloatField(default=0, help_text='0-100 confidence')
    recommendation_snapshot = models.JSONField(null=True, blank=True)
    last_optimised_at = models.DateTimeField(null=True, blank=True)
    auto_optimise_enabled = models.BooleanField(default=False)
    # Smart deposit strategy
    DEPOSIT_STRATEGY_CHOICES = [
        ('fixed', 'Fixed'),
        ('percentage', 'Percentage'),
        ('dynamic', 'Dynamic (AI Assisted)'),
    ]
    deposit_strategy = models.CharField(max_length=20, choices=DEPOSIT_STRATEGY_CHOICES, default='fixed')
    # Off-peak smart pricing
    smart_pricing_enabled = models.BooleanField(default=False)
    off_peak_discount_percent = models.FloatField(default=0)
    data_origin = models.CharField(max_length=4, choices=DATA_ORIGIN_CHOICES, default='REAL', db_index=True)
    demo_seed_id = models.UUIDField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.name} ({self.duration_minutes}min - £{self.price})"

    @property
    def price_pence(self):
        return int(self.price * 100)

    @property
    def effective_deposit_pence(self):
        if self.deposit_percentage > 0:
            return int(self.price_pence * self.deposit_percentage / 100)
        return self.deposit_pence

    @property
    def risk_indicator(self):
        """Return visual risk indicator for service table."""
        if self.no_show_rate > 15:
            return 'high_no_show'
        if self.demand_index > 80 and self.peak_utilisation_rate > 80:
            return 'high_demand'
        if self.no_show_rate > 8 or self.avg_risk_score > 50:
            return 'moderate_risk'
        return 'stable'


class ServiceOptimisationLog(models.Model):
    """Phase 6 + 9 — Commercial override and R&D logging."""
    service = models.ForeignKey('Service', on_delete=models.CASCADE, related_name='optimisation_logs')
    previous_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    new_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    previous_deposit = models.IntegerField(null=True, blank=True)
    new_deposit = models.IntegerField(null=True, blank=True)
    reason = models.TextField(blank=True, default='')
    ai_recommended = models.BooleanField(default=False)
    owner_override = models.BooleanField(default=False)
    input_metrics = models.JSONField(null=True, blank=True)
    output_recommendation = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"OptLog #{self.id} — {self.service.name} @ {self.timestamp}"


class Staff(models.Model):
    ROLE_CHOICES = [
        ('staff', 'Staff'),
        ('manager', 'Manager'),
        ('owner', 'Owner'),
    ]
    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, related_name='booking_staff')
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    photo_url = models.URLField(blank=True, help_text='URL to staff member photo')
    services = models.ManyToManyField(Service, related_name='staff_members', blank=True)
    break_start = models.TimeField(null=True, blank=True, help_text='Daily break start (e.g. lunch)')
    break_end = models.TimeField(null=True, blank=True, help_text='Daily break end')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Staff'

    def __str__(self):
        return self.name


class Client(models.Model):
    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, related_name='clients')
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    # Smart Booking Engine — reliability tracking
    total_bookings = models.IntegerField(default=0)
    completed_bookings = models.IntegerField(default=0)
    cancelled_bookings = models.IntegerField(default=0)
    no_show_count = models.IntegerField(default=0)
    consecutive_no_shows = models.IntegerField(default=0)
    last_no_show_date = models.DateTimeField(null=True, blank=True)
    reliability_score = models.FloatField(default=100.0)
    lifetime_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    avg_days_between_bookings = models.FloatField(null=True, blank=True)
    data_origin = models.CharField(max_length=4, choices=DATA_ORIGIN_CHOICES, default='REAL', db_index=True)
    demo_seed_id = models.UUIDField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.email})"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Payment Pending'),
        ('paid', 'Paid'),
        ('failed', 'Payment Failed'),
        ('refunded', 'Refunded'),
        ('credit_used', 'Credit Used'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('single_class', 'Single Class'),
        ('package', 'Class Package'),
        ('credit', 'Used Credit'),
    ]

    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, related_name='bookings')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='bookings')
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='bookings')
    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name='bookings')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    
    # Payment integration fields
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        help_text='Payment status from payment system'
    )
    payment_id = models.CharField(
        max_length=200,
        blank=True,
        help_text='Payment reference ID from payment system'
    )
    payment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Amount paid for this booking'
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        default='single_class',
        help_text='Type of payment used'
    )
    
    # Smart Booking Engine — risk & recommendation
    risk_score = models.FloatField(null=True, blank=True)
    risk_level = models.CharField(max_length=10, blank=True, default='', help_text='LOW / MEDIUM / HIGH / CRITICAL')
    revenue_at_risk = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    recommended_payment_type = models.CharField(max_length=30, blank=True, default='')
    recommended_deposit_percent = models.FloatField(null=True, blank=True)
    recommended_price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    recommended_incentive = models.CharField(max_length=200, blank=True, default='')
    recommendation_reason = models.TextField(blank=True, default='')
    optimisation_snapshot = models.JSONField(null=True, blank=True)
    override_applied = models.BooleanField(default=False)
    override_reason = models.TextField(blank=True, default='')
    data_origin = models.CharField(max_length=4, choices=DATA_ORIGIN_CHOICES, default='REAL', db_index=True)
    demo_seed_id = models.UUIDField(null=True, blank=True, db_index=True)

    # Restaurant-specific fields
    party_size = models.IntegerField(null=True, blank=True, help_text='Number of guests (restaurant bookings)')
    table = models.ForeignKey('Table', on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings', help_text='Assigned table (restaurant bookings)')

    # Email reminder tracking
    reminder_sent_24h = models.BooleanField(default=False, help_text='24-hour reminder email sent')
    reminder_sent_1h = models.BooleanField(default=False, help_text='1-hour reminder email sent')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['start_time', 'staff']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.client.name} - {self.service.name} with {self.staff.name} on {self.start_time.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        if not self.end_time:
            self.end_time = self.start_time + timezone.timedelta(minutes=self.service.duration_minutes)
        super().save(*args, **kwargs)


class OptimisationLog(models.Model):
    """R&D evidence log for all Smart Booking Engine decisions"""
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='optimisation_logs', null=True, blank=True)
    input_data = models.JSONField(null=True, blank=True)
    output_recommendation = models.JSONField(null=True, blank=True)
    override_applied = models.BooleanField(default=False)
    override_reason = models.TextField(blank=True, default='')
    reliability_score = models.FloatField(null=True, blank=True)
    risk_score = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Optimisation Log'

    def __str__(self):
        return f"Log #{self.id} booking={self.booking_id} risk={self.risk_score} @ {self.timestamp}"


class Session(models.Model):
    """Group sessions (e.g. classes, workshops)"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='sessions')
    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name='sessions')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    capacity = models.IntegerField(validators=[MinValueValidator(1)])
    enrolled_clients = models.ManyToManyField(Client, related_name='sessions', blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.title} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"

    @property
    def enrollment_count(self):
        return self.enrolled_clients.count()

    @property
    def is_full(self):
        return self.enrollment_count >= self.capacity

    @property
    def available_spots(self):
        return max(0, self.capacity - self.enrollment_count)


class BusinessHours(models.Model):
    """Business opening hours per day of week"""
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, unique=True)
    is_open = models.BooleanField(default=True)
    open_time = models.TimeField(default='09:00')
    close_time = models.TimeField(default='17:00')
    
    class Meta:
        ordering = ['day_of_week']
        verbose_name_plural = 'Business Hours'
    
    def __str__(self):
        day_name = dict(self.DAYS_OF_WEEK)[self.day_of_week]
        if not self.is_open:
            return f"{day_name}: Closed"
        return f"{day_name}: {self.open_time.strftime('%H:%M')} - {self.close_time.strftime('%H:%M')}"


class StaffSchedule(models.Model):
    """Staff member working hours per day of week"""
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    is_working = models.BooleanField(default=True)
    start_time = models.TimeField(default='09:00')
    end_time = models.TimeField(default='17:00')
    break_minutes = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['staff', 'day_of_week']
        verbose_name = 'Staff Schedule'
    
    def __str__(self):
        day_name = dict(self.DAYS_OF_WEEK)[self.day_of_week]
        if not self.is_working:
            return f"{self.staff.name} - {day_name}: Not Working"
        return f"{self.staff.name} - {day_name}: {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"


class Closure(models.Model):
    """Business closures (holidays, special events)"""
    date = models.DateField(unique=True)
    reason = models.CharField(max_length=200)
    all_day = models.BooleanField(default=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['date']
    
    def __str__(self):
        if self.all_day:
            return f"{self.date.strftime('%Y-%m-%d')}: {self.reason} (All Day)"
        return f"{self.date.strftime('%Y-%m-%d')}: {self.reason} ({self.start_time} - {self.end_time})"


class StaffBlock(models.Model):
    """Block out specific time slots when staff is unavailable"""
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='blocks')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    reason = models.CharField(max_length=200, blank=True)
    all_day = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']
        verbose_name = 'Staff Block'

    def __str__(self):
        if self.all_day:
            return f"{self.staff.name} - {self.date}: Blocked all day ({self.reason})"
        return f"{self.staff.name} - {self.date}: {self.start_time} - {self.end_time} ({self.reason})"


class StaffLeave(models.Model):
    """Individual staff member time off"""
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='leave')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['start_date']
        verbose_name = 'Staff Leave'
        verbose_name_plural = 'Staff Leave'
    
    def __str__(self):
        if self.start_date == self.end_date:
            return f"{self.staff.name} - {self.start_date.strftime('%Y-%m-%d')}"
        return f"{self.staff.name} - {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}"
