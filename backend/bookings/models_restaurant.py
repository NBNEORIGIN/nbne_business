"""
Restaurant-specific models — Table inventory and Service Windows.
Used when tenant.business_type == 'restaurant'.
"""
from django.db import models
from django.core.validators import MinValueValidator


WEEKDAY_CHOICES = [
    (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
    (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
]


class Table(models.Model):
    """Physical table in the restaurant."""
    tenant = models.ForeignKey(
        'tenants.TenantSettings', on_delete=models.CASCADE, related_name='tables'
    )
    name = models.CharField(max_length=100, help_text='e.g. Table 1, Window Booth, Terrace 3')
    min_seats = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    max_seats = models.IntegerField(default=4, validators=[MinValueValidator(1)])
    combinable = models.BooleanField(default=False, help_text='Can be combined with adjacent table')
    combine_with = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        help_text='Adjacent table for combining',
    )
    zone = models.CharField(max_length=100, blank=True, default='', help_text='e.g. Main, Terrace, Private')
    active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.name} ({self.min_seats}-{self.max_seats} seats)"


class ServiceWindow(models.Model):
    """A bookable time window — e.g. Lunch 12:00-14:30, Dinner 18:00-22:00."""
    tenant = models.ForeignKey(
        'tenants.TenantSettings', on_delete=models.CASCADE, related_name='service_windows'
    )
    name = models.CharField(max_length=100, help_text='e.g. Lunch, Dinner, Brunch')
    day_of_week = models.IntegerField(choices=WEEKDAY_CHOICES)
    open_time = models.TimeField()
    close_time = models.TimeField()
    last_booking_time = models.TimeField(help_text='Latest time a booking can start')
    turn_time_minutes = models.IntegerField(
        default=90, validators=[MinValueValidator(15)],
        help_text='Default dining duration in minutes',
    )
    max_covers = models.IntegerField(
        default=50, validators=[MinValueValidator(1)],
        help_text='Max total covers in this window',
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day_of_week', 'open_time']

    def __str__(self):
        day = dict(WEEKDAY_CHOICES).get(self.day_of_week, '?')
        return f"{self.name} — {day} {self.open_time:%H:%M}–{self.close_time:%H:%M}"
