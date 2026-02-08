from django.conf import settings
from django.db import models


class IncidentReport(models.Model):
    SEVERITY_CHOICES = [('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('CRITICAL', 'Critical')]
    STATUS_CHOICES = [('OPEN', 'Open'), ('INVESTIGATING', 'Investigating'), ('RESOLVED', 'Resolved'), ('CLOSED', 'Closed')]

    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM', db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN', db_index=True)
    location = models.CharField(max_length=255, blank=True, default='')
    incident_date = models.DateTimeField(db_index=True)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='reported_incidents')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_incidents')
    resolution_notes = models.TextField(blank=True, default='')
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'compliance_incident_report'
        ordering = ['-incident_date']

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.title}"


class IncidentPhoto(models.Model):
    incident = models.ForeignKey(IncidentReport, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='compliance/incidents/%Y/%m/')
    caption = models.CharField(max_length=255, blank=True, default='')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_incident_photo'

    def __str__(self):
        return f"Photo for {self.incident.title}"


class SignOff(models.Model):
    incident = models.ForeignKey(IncidentReport, on_delete=models.CASCADE, related_name='sign_offs')
    signed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    role = models.CharField(max_length=100, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    signed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_sign_off'
        ordering = ['-signed_at']

    def __str__(self):
        signer = self.signed_by.get_full_name() if self.signed_by else 'Unknown'
        return f"Sign-off by {signer} on {self.incident.title}"


class RAMSDocument(models.Model):
    STATUS_CHOICES = [('DRAFT', 'Draft'), ('ACTIVE', 'Active'), ('EXPIRED', 'Expired'), ('ARCHIVED', 'Archived')]

    title = models.CharField(max_length=255)
    reference_number = models.CharField(max_length=100, blank=True, default='', db_index=True)
    description = models.TextField(blank=True, default='')
    document = models.FileField(upload_to='compliance/rams/%Y/%m/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', db_index=True)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True, db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_rams')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'compliance_rams_document'
        ordering = ['-created_at']
        verbose_name = 'RAMS Document'
        verbose_name_plural = 'RAMS Documents'

    def __str__(self):
        return f"{self.title} ({self.reference_number})" if self.reference_number else self.title

    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()
