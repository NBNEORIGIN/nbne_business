"""
Staff Availability Engine — Models
Rule-based availability supporting split shifts, overrides, leave, blocks, shifts, and timesheets.
Designed to power booking slot generation reliably for UK small businesses.
"""
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import time


# ─────────────────────────────────────────────────────────────────────
# A) WorkingPattern — named weekly template per staff member
# ─────────────────────────────────────────────────────────────────────
class WorkingPattern(models.Model):
    staff_member = models.ForeignKey(
        'Staff', on_delete=models.CASCADE, related_name='working_patterns'
    )
    name = models.CharField(max_length=120, default='Default')
    timezone = models.CharField(max_length=50, default='Europe/London')
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_active', '-created_at']

    def __str__(self):
        return f"{self.staff_member.name} — {self.name}"

    def clean(self):
        if self.effective_from and self.effective_to:
            if self.effective_to < self.effective_from:
                raise ValidationError('effective_to must be >= effective_from')


# ─────────────────────────────────────────────────────────────────────
# B) WorkingPatternRule — split-shift periods within a weekday
# ─────────────────────────────────────────────────────────────────────
WEEKDAY_CHOICES = [
    (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
    (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
]


class WorkingPatternRule(models.Model):
    working_pattern = models.ForeignKey(
        WorkingPattern, on_delete=models.CASCADE, related_name='rules'
    )
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['weekday', 'sort_order', 'start_time']

    def __str__(self):
        day = dict(WEEKDAY_CHOICES).get(self.weekday, '?')
        return f"{day} {self.start_time:%H:%M}–{self.end_time:%H:%M}"

    def clean(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError('end_time must be after start_time')
        # Overlap check within same (pattern, weekday)
        if self.working_pattern_id and self.weekday is not None:
            siblings = WorkingPatternRule.objects.filter(
                working_pattern=self.working_pattern,
                weekday=self.weekday,
            ).exclude(pk=self.pk)
            for sib in siblings:
                if self.start_time < sib.end_time and self.end_time > sib.start_time:
                    raise ValidationError(
                        f'Overlaps with existing period {sib.start_time:%H:%M}–{sib.end_time:%H:%M}'
                    )


# ─────────────────────────────────────────────────────────────────────
# C) AvailabilityOverride — one-off date override
# ─────────────────────────────────────────────────────────────────────
OVERRIDE_MODE_CHOICES = [
    ('REPLACE', 'Replace (override full day)'),
    ('ADD', 'Add (union with weekly)'),
    ('REMOVE', 'Remove (subtract from weekly)'),
    ('CLOSED', 'Closed (no work that day)'),
]


class AvailabilityOverride(models.Model):
    staff_member = models.ForeignKey(
        'Staff', on_delete=models.CASCADE, related_name='availability_overrides'
    )
    date = models.DateField()
    mode = models.CharField(max_length=10, choices=OVERRIDE_MODE_CHOICES)
    reason = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_overrides',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date']
        unique_together = ['staff_member', 'date']

    def __str__(self):
        return f"{self.staff_member.name} {self.date} [{self.mode}]"


# ─────────────────────────────────────────────────────────────────────
# D) AvailabilityOverridePeriod — time ranges within an override
# ─────────────────────────────────────────────────────────────────────
class AvailabilityOverridePeriod(models.Model):
    availability_override = models.ForeignKey(
        AvailabilityOverride, on_delete=models.CASCADE, related_name='periods'
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'start_time']

    def __str__(self):
        return f"{self.start_time:%H:%M}–{self.end_time:%H:%M}"

    def clean(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError('end_time must be after start_time')
        # CLOSED mode must have no periods
        if self.availability_override_id:
            override = self.availability_override
            if override.mode == 'CLOSED':
                raise ValidationError('CLOSED overrides must not have periods')


# ─────────────────────────────────────────────────────────────────────
# E) LeaveRequest
# ─────────────────────────────────────────────────────────────────────
LEAVE_TYPE_CHOICES = [
    ('ANNUAL', 'Annual Leave'),
    ('SICK', 'Sick Leave'),
    ('UNPAID', 'Unpaid Leave'),
    ('OTHER', 'Other'),
]

LEAVE_STATUS_CHOICES = [
    ('REQUESTED', 'Requested'),
    ('APPROVED', 'Approved'),
    ('REJECTED', 'Rejected'),
    ('CANCELLED', 'Cancelled'),
]


class LeaveRequest(models.Model):
    staff_member = models.ForeignKey(
        'Staff', on_delete=models.CASCADE, related_name='leave_requests'
    )
    leave_type = models.CharField(max_length=10, choices=LEAVE_TYPE_CHOICES)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    status = models.CharField(max_length=10, choices=LEAVE_STATUS_CHOICES, default='REQUESTED')
    reason = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_leave_requests',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_leave_requests',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_datetime']

    def __str__(self):
        return f"{self.staff_member.name} {self.leave_type} {self.start_datetime:%Y-%m-%d} [{self.status}]"

    def clean(self):
        if self.start_datetime and self.end_datetime:
            if self.end_datetime <= self.start_datetime:
                raise ValidationError('end_datetime must be after start_datetime')


# ─────────────────────────────────────────────────────────────────────
# F) BlockedTime — ad-hoc blocks (staff-specific or global)
# ─────────────────────────────────────────────────────────────────────
class BlockedTime(models.Model):
    staff_member = models.ForeignKey(
        'Staff', on_delete=models.CASCADE, null=True, blank=True,
        related_name='blocked_times',
        help_text='Null = applies to ALL staff',
    )
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    reason = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_blocked_times',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_datetime']

    def __str__(self):
        who = self.staff_member.name if self.staff_member else 'ALL STAFF'
        return f"Block {who} {self.start_datetime:%Y-%m-%d %H:%M}–{self.end_datetime:%H:%M}"

    def clean(self):
        if self.start_datetime and self.end_datetime:
            if self.end_datetime <= self.start_datetime:
                raise ValidationError('end_datetime must be after start_datetime')


# ─────────────────────────────────────────────────────────────────────
# G) Shift (rota)
# ─────────────────────────────────────────────────────────────────────
class Shift(models.Model):
    staff_member = models.ForeignKey(
        'Staff', on_delete=models.CASCADE, related_name='shifts'
    )
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True, default='')
    published = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_datetime']

    def __str__(self):
        return f"{self.staff_member.name} shift {self.start_datetime:%Y-%m-%d %H:%M}–{self.end_datetime:%H:%M}"

    def clean(self):
        if self.start_datetime and self.end_datetime:
            if self.end_datetime <= self.start_datetime:
                raise ValidationError('end_datetime must be after start_datetime')


# ─────────────────────────────────────────────────────────────────────
# H) TimesheetEntry
# ─────────────────────────────────────────────────────────────────────
TIMESHEET_STATUS_CHOICES = [
    ('DRAFT', 'Draft'),
    ('SUBMITTED', 'Submitted'),
    ('APPROVED', 'Approved'),
]

TIMESHEET_SOURCE_CHOICES = [
    ('MANUAL', 'Manual Entry'),
    ('CLOCK_IN_OUT', 'Clock In/Out'),
    ('GENERATED_FROM_SHIFT', 'Generated from Shift'),
    ('GENERATED_FROM_PATTERN', 'Generated from Pattern'),
]


class TimesheetEntry(models.Model):
    staff_member = models.ForeignKey(
        'Staff', on_delete=models.CASCADE, related_name='timesheet_entries'
    )
    date = models.DateField()
    scheduled_start = models.DateTimeField(null=True, blank=True)
    scheduled_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    break_minutes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=10, choices=TIMESHEET_STATUS_CHOICES, default='DRAFT')
    source = models.CharField(max_length=30, choices=TIMESHEET_SOURCE_CHOICES, default='MANUAL')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['staff_member', 'date']

    def __str__(self):
        return f"{self.staff_member.name} {self.date} [{self.status}]"

    @property
    def scheduled_hours(self):
        if self.scheduled_start and self.scheduled_end:
            delta = (self.scheduled_end - self.scheduled_start).total_seconds() / 3600
            return round(max(0, delta - self.break_minutes / 60), 2)
        return None

    @property
    def actual_hours(self):
        if self.actual_start and self.actual_end:
            delta = (self.actual_end - self.actual_start).total_seconds() / 3600
            return round(max(0, delta - self.break_minutes / 60), 2)
        return None

    @property
    def variance(self):
        s = self.scheduled_hours
        a = self.actual_hours
        if s is not None and a is not None:
            return round(a - s, 2)
        return None
