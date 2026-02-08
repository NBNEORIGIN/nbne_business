from django.contrib import admin
from .models import Document, DocumentTag


@admin.register(DocumentTag)
class DocumentTagAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'tier_access', 'uploaded_by', 'expiry_date', 'is_active']
    list_filter = ['category', 'tier_access', 'is_active']
    search_fields = ['title']
