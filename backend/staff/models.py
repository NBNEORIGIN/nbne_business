from django.conf import settings
from django.db import models


class StaffProfile(models.Model):
    """Extended profile for a staff member, linked to custom User."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='staff_profile')
    display_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True, default='')
    emergency_contact_name = models.CharField(max_length=255, blank=True, default='')
    emergency_contact_phone = models.CharField(max_length=50, blank=True, default='')
    hire_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'staff_profile'
        ordering = ['display_name']

    def __str__(self):
        return f"{self.display_name} ({self.user.role})"


class Shift(models.Model):
    """A scheduled shift for a staff member."""
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='shifts')
    date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=255, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    is_published = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'staff_shift'
        ordering = ['date', 'start_time']
        indexes = [models.Index(fields=['staff', 'date'])]

    def __str__(self):
        return f"{self.staff.display_name} — {self.date} {self.start_time}-{self.end_time}"

    @property
    def duration_hours(self):
        from datetime import datetime, timedelta
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        if end < start:
            end += timedelta(days=1)
        return (end - start).total_seconds() / 3600


class LeaveRequest(models.Model):
    STATUS_CHOICES = [('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('CANCELLED', 'Cancelled')]
    TYPE_CHOICES = [('ANNUAL', 'Annual Leave'), ('SICK', 'Sick Leave'), ('UNPAID', 'Unpaid Leave'), ('OTHER', 'Other')]

    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='ANNUAL')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    reviewed_by = models.ForeignKey(StaffProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_leave_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'staff_leave_request'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.staff.display_name} — {self.get_leave_type_display()} {self.start_date} to {self.end_date}"

    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days + 1


class TrainingRecord(models.Model):
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='training_records')
    title = models.CharField(max_length=255)
    provider = models.CharField(max_length=255, blank=True, default='')
    completed_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True, db_index=True)
    certificate_reference = models.CharField(max_length=255, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'staff_training_record'
        ordering = ['-completed_date']

    def __str__(self):
        return f"{self.staff.display_name} — {self.title}"

    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()


class WorkingHours(models.Model):
    """Recurring weekly working hours for a staff member. Supports split shifts via multiple rows per day."""
    DAY_CHOICES = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='working_hours')
    day_of_week = models.IntegerField(choices=DAY_CHOICES, db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_minutes = models.PositiveIntegerField(default=0, help_text='Unpaid break in minutes')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'staff_working_hours'
        ordering = ['staff', 'day_of_week', 'start_time']
        indexes = [models.Index(fields=['staff', 'day_of_week'])]

    def __str__(self):
        return f"{self.staff.display_name} — {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

    @property
    def scheduled_hours(self):
        from datetime import datetime, timedelta
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        if end < start:
            end += timedelta(days=1)
        return max(0, (end - start).total_seconds() / 3600 - self.break_minutes / 60)


class TimesheetEntry(models.Model):
    """Daily timesheet entry per staff. Auto-populated from WorkingHours, editable by managers."""
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('WORKED', 'Worked'),
        ('LATE', 'Late Arrival'),
        ('LEFT_EARLY', 'Left Early'),
        ('ABSENT', 'Absent'),
        ('SICK', 'Sick'),
        ('HOLIDAY', 'Holiday'),
        ('AMENDED', 'Amended'),
    ]
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='timesheet_entries')
    date = models.DateField(db_index=True)
    scheduled_start = models.TimeField(null=True, blank=True)
    scheduled_end = models.TimeField(null=True, blank=True)
    scheduled_break_minutes = models.PositiveIntegerField(default=0)
    actual_start = models.TimeField(null=True, blank=True)
    actual_end = models.TimeField(null=True, blank=True)
    actual_break_minutes = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED', db_index=True)
    notes = models.TextField(blank=True, default='')
    approved_by = models.ForeignKey(StaffProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_timesheets')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'staff_timesheet'
        ordering = ['-date', 'staff__display_name']
        unique_together = ['staff', 'date']
        indexes = [models.Index(fields=['staff', 'date'])]

    def __str__(self):
        return f"{self.staff.display_name} — {self.date} ({self.get_status_display()})"

    @property
    def scheduled_hours(self):
        if not self.scheduled_start or not self.scheduled_end:
            return 0
        from datetime import datetime, timedelta
        start = datetime.combine(self.date, self.scheduled_start)
        end = datetime.combine(self.date, self.scheduled_end)
        if end < start:
            end += timedelta(days=1)
        return max(0, (end - start).total_seconds() / 3600 - self.scheduled_break_minutes / 60)

    @property
    def actual_hours(self):
        if not self.actual_start or not self.actual_end:
            return 0
        from datetime import datetime, timedelta
        start = datetime.combine(self.date, self.actual_start)
        end = datetime.combine(self.date, self.actual_end)
        if end < start:
            end += timedelta(days=1)
        return max(0, (end - start).total_seconds() / 3600 - self.actual_break_minutes / 60)

    @property
    def variance_hours(self):
        return round(self.actual_hours - self.scheduled_hours, 2)


class AbsenceRecord(models.Model):
    TYPE_CHOICES = [('ABSENCE', 'Absence'), ('LATENESS', 'Lateness')]

    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='absence_records')
    record_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='ABSENCE')
    date = models.DateField(db_index=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    reason = models.TextField(blank=True, default='')
    is_authorised = models.BooleanField(default=False)
    recorded_by = models.ForeignKey(StaffProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='recorded_absences')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'staff_absence_record'
        ordering = ['-date']

    def __str__(self):
        return f"{self.staff.display_name} — {self.get_record_type_display()} {self.date}"
