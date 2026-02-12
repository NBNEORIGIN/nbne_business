from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# 1. ComplianceCategory — UK H&S compliance areas
# ---------------------------------------------------------------------------
class ComplianceCategory(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    legal_requirement = models.BooleanField(default=False, help_text='Is this a legal requirement under UK law?')
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_category'
        ordering = ['order', 'name']
        verbose_name = 'Compliance Category'
        verbose_name_plural = 'Compliance Categories'

    def __str__(self):
        prefix = '⚖️' if self.legal_requirement else '✓'
        return f"{prefix} {self.name}"


# ---------------------------------------------------------------------------
# 2. ComplianceItem — individual compliance obligations with scheduling
# ---------------------------------------------------------------------------
class ComplianceItem(models.Model):
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
        ('3_year', 'Every 3 Years'),
        ('5_year', 'Every 5 Years'),
        ('custom_days', 'Custom (days)'),
        ('one_off', 'One-off'),
    ]
    STATUS_CHOICES = [
        ('compliant', 'Compliant'),
        ('due_soon', 'Due Soon'),
        ('overdue', 'Overdue'),
        ('not_started', 'Not Started'),
    ]

    title = models.CharField(max_length=255)
    category = models.ForeignKey(ComplianceCategory, on_delete=models.CASCADE, related_name='items')
    description = models.TextField(blank=True, default='')
    frequency_type = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='annual')
    frequency_days = models.IntegerField(null=True, blank=True, help_text='Custom frequency in days (only for custom_days)')
    last_completed_date = models.DateField(null=True, blank=True)
    next_due_date = models.DateField(null=True, blank=True, db_index=True)
    responsible_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='compliance_responsibilities',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started', db_index=True)
    is_baseline = models.BooleanField(default=False, help_text='Auto-created UK baseline item')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'compliance_item'
        ordering = ['next_due_date', 'title']
        verbose_name = 'Compliance Item'
        verbose_name_plural = 'Compliance Items'

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    @property
    def frequency_in_days(self):
        mapping = {
            'weekly': 7,
            'monthly': 30,
            'annual': 365,
            '3_year': 1095,
            '5_year': 1825,
            'custom_days': self.frequency_days,
            'one_off': None,
        }
        return mapping.get(self.frequency_type)

    def calculate_next_due(self):
        if self.frequency_type == 'one_off':
            return None
        days = self.frequency_in_days
        if days and self.last_completed_date:
            return self.last_completed_date + timedelta(days=days)
        return self.next_due_date

    def update_status(self):
        today = timezone.now().date()
        if not self.next_due_date:
            if not self.last_completed_date:
                self.status = 'not_started'
            return
        if self.next_due_date < today:
            self.status = 'overdue'
        elif self.next_due_date <= today + timedelta(days=30):
            self.status = 'due_soon'
        else:
            self.status = 'compliant'

    def mark_completed(self, completed_date=None):
        self.last_completed_date = completed_date or timezone.now().date()
        self.next_due_date = self.calculate_next_due()
        self.update_status()
        self.save()

    def save(self, *args, **kwargs):
        if self.next_due_date is None and self.last_completed_date:
            self.next_due_date = self.calculate_next_due()
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# 3. IncidentReport — with UK RIDDOR fields
# ---------------------------------------------------------------------------
class IncidentReport(models.Model):
    SEVERITY_CHOICES = [('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('CRITICAL', 'Critical')]
    STATUS_CHOICES = [('OPEN', 'Open'), ('INVESTIGATING', 'Investigating'), ('RESOLVED', 'Resolved'), ('CLOSED', 'Closed')]
    INJURY_CHOICES = [
        ('none', 'No Injury'),
        ('minor', 'Minor Injury'),
        ('major', 'Major Injury'),
        ('fatality', 'Fatality'),
        ('disease', 'Occupational Disease'),
        ('dangerous_occurrence', 'Dangerous Occurrence'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM', db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN', db_index=True)
    location = models.CharField(max_length=255, blank=True, default='')
    incident_date = models.DateTimeField(db_index=True)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='reported_incidents')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_incidents')
    injury_type = models.CharField(max_length=30, choices=INJURY_CHOICES, default='none')
    riddor_reportable = models.BooleanField(default=False, help_text='Reportable under RIDDOR 2013?')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_incidents',
    )
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


# ---------------------------------------------------------------------------
# 4. TrainingRecord — staff training with certificate tracking
# ---------------------------------------------------------------------------
class TrainingRecord(models.Model):
    TRAINING_TYPE_CHOICES = [
        ('first_aid', 'First Aid at Work'),
        ('fire_marshal', 'Fire Marshal'),
        ('manual_handling', 'Manual Handling'),
        ('coshh', 'COSHH'),
        ('food_hygiene', 'Food Hygiene'),
        ('safeguarding', 'Safeguarding'),
        ('dse', 'Display Screen Equipment'),
        ('working_at_height', 'Working at Height'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='training_records')
    training_type = models.CharField(max_length=30, choices=TRAINING_TYPE_CHOICES)
    title = models.CharField(max_length=255, blank=True, default='', help_text='Custom title if type is "other"')
    provider = models.CharField(max_length=255, blank=True, default='')
    certificate_file = models.FileField(upload_to='compliance/training/%Y/%m/', blank=True, null=True)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True, db_index=True)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'compliance_training_record'
        ordering = ['expiry_date', 'user']
        verbose_name = 'Training Record'
        verbose_name_plural = 'Training Records'

    def __str__(self):
        name = self.user.get_full_name() if self.user else 'Unknown'
        return f"{name} — {self.get_training_type_display()}"

    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        return self.expiry_date < timezone.now().date()

    @property
    def is_expiring_soon(self):
        if not self.expiry_date:
            return False
        return self.expiry_date <= timezone.now().date() + timedelta(days=30)

    @property
    def status(self):
        if self.is_expired:
            return 'expired'
        if self.is_expiring_soon:
            return 'expiring_soon'
        return 'valid'


# ---------------------------------------------------------------------------
# 5. DocumentVault — versioned document storage
# ---------------------------------------------------------------------------
class DocumentVault(models.Model):
    DOC_TYPE_CHOICES = [
        ('policy', 'Policy'),
        ('certificate', 'Certificate'),
        ('risk_assessment', 'Risk Assessment'),
        ('insurance', 'Insurance'),
        ('license', 'License'),
        ('training_material', 'Training Material'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='compliance/vault/%Y/%m/')
    document_type = models.CharField(max_length=30, choices=DOC_TYPE_CHOICES, default='other', db_index=True)
    description = models.TextField(blank=True, default='')
    expiry_date = models.DateField(null=True, blank=True, db_index=True)
    version = models.CharField(max_length=20, default='1.0')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='vault_uploads')
    supersedes = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='superseded_by')
    is_current = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'compliance_document_vault'
        ordering = ['-created_at']
        verbose_name = 'Document'
        verbose_name_plural = 'Document Vault'

    def __str__(self):
        return f"{self.title} v{self.version}"

    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        return self.expiry_date < timezone.now().date()

    def upload_new_version(self, file, uploaded_by, new_version=None):
        self.is_current = False
        self.save(update_fields=['is_current'])
        parts = self.version.split('.')
        if new_version:
            ver = new_version
        else:
            ver = f"{int(parts[0]) + 1}.0" if len(parts) == 1 else f"{parts[0]}.{int(parts[1]) + 1}"
        return DocumentVault.objects.create(
            title=self.title,
            file=file,
            document_type=self.document_type,
            description=self.description,
            expiry_date=self.expiry_date,
            version=ver,
            uploaded_by=uploaded_by,
            supersedes=self,
            is_current=True,
        )


# ---------------------------------------------------------------------------
# 6. ComplianceActionLog — audit trail for all compliance actions
# ---------------------------------------------------------------------------
class ComplianceActionLog(models.Model):
    ACTION_CHOICES = [
        ('completed', 'Marked Completed'),
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('status_change', 'Status Changed'),
        ('reminder_sent', 'Reminder Sent'),
        ('document_uploaded', 'Document Uploaded'),
        ('reviewed', 'Reviewed'),
        ('assigned', 'Assigned'),
    ]

    compliance_item = models.ForeignKey(ComplianceItem, on_delete=models.CASCADE, null=True, blank=True, related_name='action_logs')
    incident = models.ForeignKey(IncidentReport, on_delete=models.CASCADE, null=True, blank=True, related_name='action_logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'compliance_action_log'
        ordering = ['-timestamp']
        verbose_name = 'Action Log'
        verbose_name_plural = 'Action Logs'

    def __str__(self):
        target = self.compliance_item or self.incident or 'General'
        return f"{self.get_action_display()} — {target} by {self.user}"


# ---------------------------------------------------------------------------
# 7. RAMSDocument — preserved from original
# ---------------------------------------------------------------------------
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
        return self.expiry_date < timezone.now().date()
