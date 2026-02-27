from django.conf import settings
from django.db import models


class DocumentTag(models.Model):
    """Tag for categorising documents."""
    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, related_name='document_tags')
    name = models.CharField(max_length=100)
    colour = models.CharField(max_length=50, blank=True, default='', help_text='Optional CSS colour')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Document(models.Model):
    """A securely stored document with optional expiry and category."""
    # Default categories provided as suggestions — tenants can add their own
    DEFAULT_CATEGORIES = [
        'Legal', 'Policy', 'Insurance', 'Compliance',
        'Training', 'Health & Safety', 'HR', 'Contract', 'General',
    ]
    ACCESS_CHOICES = [
        ('owner', 'Owner Only'),
        ('manager', 'Manager+'),
        ('staff', 'All Staff'),
    ]

    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    category = models.CharField(max_length=100, blank=True, default='General', db_index=True)
    file = models.FileField(upload_to='vault/%Y/%m/', null=True, blank=True)
    filename = models.CharField(max_length=255, blank=True, default='')
    content_type = models.CharField(max_length=100, blank=True, default='')
    size_bytes = models.PositiveIntegerField(default=0)
    tags = models.ManyToManyField(DocumentTag, related_name='documents', blank=True)
    expiry_date = models.DateField(null=True, blank=True, db_index=True)
    reminder_days_before = models.PositiveIntegerField(
        default=30, help_text='Days before expiry to trigger reminder'
    )
    access_level = models.CharField(max_length=20, choices=ACCESS_CHOICES, default='staff')
    is_archived = models.BooleanField(default=False, db_index=True)
    is_placeholder = models.BooleanField(
        default=False, db_index=True,
        help_text='True if this is a required-document placeholder (no file uploaded yet)'
    )
    regulatory_ref = models.CharField(
        max_length=500, blank=True, default='',
        help_text='Legal/regulatory reference e.g. Health and Safety at Work Act 1974'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='vault_documents'
    )
    linked_staff = models.ForeignKey(
        'bookings.Staff', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='vault_documents',
        help_text='Optional link to a staff member (for training certs)'
    )
    # Link to compliance items / H&S documents
    compliance_item = models.ForeignKey(
        'compliance.ComplianceItem', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='vault_documents',
        help_text='Link to a compliance register item'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', '-created_at']

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()

    @property
    def is_expiring_soon(self):
        if not self.expiry_date:
            return False
        from django.utils import timezone
        from datetime import timedelta
        today = timezone.now().date()
        threshold = today + timedelta(days=self.reminder_days_before)
        return self.expiry_date <= threshold and not self.is_expired

    @property
    def status(self):
        if self.is_placeholder and not self.file:
            return 'MISSING'
        if self.is_expired:
            return 'EXPIRED'
        if self.is_expiring_soon:
            return 'EXPIRING'
        return 'VALID'

    @property
    def file_size_display(self):
        if self.size_bytes == 0:
            return ''
        if self.size_bytes < 1024:
            return f'{self.size_bytes} B'
        elif self.size_bytes < 1024 * 1024:
            return f'{self.size_bytes / 1024:.0f} KB'
        else:
            return f'{self.size_bytes / (1024 * 1024):.1f} MB'
