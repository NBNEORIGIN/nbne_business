from django.conf import settings
from django.db import models


class DocumentTag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'documents_tag'
        ordering = ['name']

    def __str__(self):
        return self.name


class Document(models.Model):
    CATEGORY_CHOICES = [
        ('POLICY', 'Policy'), ('PROCEDURE', 'Procedure'), ('FORM', 'Form'),
        ('CERTIFICATE', 'Certificate'), ('CONTRACT', 'Contract'),
        ('TRAINING', 'Training'), ('HSE', 'HSE'), ('OTHER', 'Other'),
    ]
    ACCESS_CHOICES = [
        ('customer', 'Customer+'), ('staff', 'Staff+'), ('manager', 'Manager+'), ('owner', 'Owner Only'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHER', db_index=True)
    file = models.FileField(upload_to='documents/%Y/%m/')
    file_size = models.CharField(max_length=50, blank=True, default='')
    tier_access = models.CharField(max_length=20, choices=ACCESS_CHOICES, default='staff')
    tags = models.ManyToManyField(DocumentTag, related_name='documents', blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents')
    expiry_date = models.DateField(null=True, blank=True, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'documents_document'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()
