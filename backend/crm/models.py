from django.conf import settings
from django.db import models


class Lead(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New'), ('CONTACTED', 'Contacted'), ('QUALIFIED', 'Qualified'),
        ('CONVERTED', 'Converted'), ('LOST', 'Lost'),
    ]
    SOURCE_CHOICES = [
        ('WEBSITE', 'Website'), ('REFERRAL', 'Referral'), ('SOCIAL', 'Social Media'),
        ('WALK_IN', 'Walk-in'), ('PHONE', 'Phone'), ('OTHER', 'Other'),
    ]

    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, default='')
    phone = models.CharField(max_length=50, blank=True, default='')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='WEBSITE', db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW', db_index=True)
    value_pence = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True, default='')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_leads')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_leads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'crm_lead'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class LeadNote(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='lead_notes')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crm_lead_note'
        ordering = ['-created_at']

    def __str__(self):
        return f"Note on {self.lead.name} by {self.author}"


class FollowUp(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='follow_ups')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    due_date = models.DateField(db_index=True)
    description = models.TextField(blank=True, default='')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crm_follow_up'
        ordering = ['due_date']

    def __str__(self):
        return f"Follow-up for {self.lead.name} due {self.due_date}"
