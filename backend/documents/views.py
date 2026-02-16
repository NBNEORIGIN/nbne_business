from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status, serializers
from django.utils import timezone
from datetime import timedelta
from .models import Document, DocumentTag


# ── Serializers ──────────────────────────────────────────────

class DocumentTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentTag
        fields = ['id', 'name', 'colour']


class DocumentSerializer(serializers.ModelSerializer):
    tags = DocumentTagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=DocumentTag.objects.all(), many=True, write_only=True, required=False, source='tags'
    )
    uploaded_by_name = serializers.SerializerMethodField()
    linked_staff_name = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)
    is_expiring_soon = serializers.BooleanField(read_only=True)
    status = serializers.CharField(read_only=True)
    file_size_display = serializers.CharField(read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'category', 'file', 'file_url',
            'filename', 'content_type', 'size_bytes', 'file_size_display',
            'tags', 'tag_ids', 'expiry_date', 'reminder_days_before',
            'access_level', 'is_expired', 'is_expiring_soon', 'status',
            'is_archived', 'is_placeholder', 'regulatory_ref',
            'uploaded_by', 'uploaded_by_name',
            'linked_staff', 'linked_staff_name',
            'compliance_item',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'uploaded_by', 'uploaded_by_name', 'is_expired',
            'is_expiring_soon', 'status', 'file_size_display', 'file_url',
            'created_at', 'updated_at',
        ]

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
        return None

    def get_linked_staff_name(self, obj):
        if obj.linked_staff:
            return obj.linked_staff.display_name or obj.linked_staff.user.get_full_name()
        return None

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None


# ── Views ────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_list(request):
    """List documents with optional filters."""
    tenant = getattr(request, 'tenant', None)
    docs = Document.objects.filter(tenant=tenant).prefetch_related('tags').select_related('uploaded_by', 'linked_staff')

    # Exclude archived by default
    archived = request.query_params.get('archived')
    if not archived or archived.lower() != 'true':
        docs = docs.filter(is_archived=False)

    category = request.query_params.get('category')
    if category:
        docs = docs.filter(category=category.upper())

    tag = request.query_params.get('tag')
    if tag:
        docs = docs.filter(tags__name__iexact=tag)

    expired = request.query_params.get('expired')
    if expired and expired.lower() == 'true':
        docs = docs.filter(expiry_date__lt=timezone.now().date())

    expiring = request.query_params.get('expiring')
    if expiring and expiring.lower() == 'true':
        today = timezone.now().date()
        docs = docs.filter(expiry_date__gt=today, expiry_date__lte=today + timedelta(days=30))

    placeholder = request.query_params.get('placeholder')
    if placeholder and placeholder.lower() == 'true':
        docs = docs.filter(is_placeholder=True, file='')

    search = request.query_params.get('search')
    if search:
        docs = docs.filter(title__icontains=search)

    return Response(DocumentSerializer(docs[:200], many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def document_create(request):
    """Upload a new document."""
    serializer = DocumentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    tenant = getattr(request, 'tenant', None)
    doc = serializer.save(uploaded_by=request.user, tenant=tenant)

    # Auto-populate filename and size from uploaded file
    if doc.file:
        if not doc.filename:
            doc.filename = doc.file.name.split('/')[-1]
        if not doc.size_bytes:
            try:
                doc.size_bytes = doc.file.size
            except Exception:
                pass
        doc.save(update_fields=['filename', 'size_bytes'])

    return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def document_detail(request, doc_id):
    """Get, update, or delete a document."""
    try:
        tenant = getattr(request, 'tenant', None)
        doc = Document.objects.filter(tenant=tenant).prefetch_related('tags').select_related('uploaded_by', 'linked_staff').get(id=doc_id)
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(DocumentSerializer(doc).data)

    if request.method == 'DELETE':
        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # PATCH
    serializer = DocumentSerializer(doc, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    doc = serializer.save()

    # Update filename/size if new file uploaded
    if 'file' in request.data and doc.file:
        doc.filename = doc.file.name.split('/')[-1]
        try:
            doc.size_bytes = doc.file.size
        except Exception:
            pass
        if doc.is_placeholder:
            doc.is_placeholder = False
        doc.save(update_fields=['filename', 'size_bytes', 'is_placeholder'])

    return Response(DocumentSerializer(doc).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_summary(request):
    """Summary stats for the document vault."""
    tenant = getattr(request, 'tenant', None)
    docs = Document.objects.filter(tenant=tenant, is_archived=False)
    today = timezone.now().date()

    total = docs.count()
    valid = docs.filter(
        models_Q_valid(today)
    ).count()
    expired = docs.filter(expiry_date__lt=today).count()
    expiring = docs.filter(expiry_date__gt=today, expiry_date__lte=today + timedelta(days=30)).count()
    missing = docs.filter(is_placeholder=True, file='').count()

    # Category breakdown
    from django.db.models import Count
    categories = list(
        docs.values('category').annotate(count=Count('id')).order_by('category')
    )

    return Response({
        'total': total,
        'valid': total - expired - expiring - missing,
        'expired': expired,
        'expiring_soon': expiring,
        'missing': missing,
        'categories': categories,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def expiry_reminders(request):
    """List documents expiring within their reminder window."""
    today = timezone.now().date()
    tenant = getattr(request, 'tenant', None)
    docs = Document.objects.filter(
        tenant=tenant,
        is_archived=False,
        expiry_date__isnull=False,
        expiry_date__gt=today,
    ).prefetch_related('tags')

    expiring = [d for d in docs if d.is_expiring_soon]
    return Response(DocumentSerializer(expiring, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tag_list(request):
    """List all document tags."""
    tenant = getattr(request, 'tenant', None)
    tags = DocumentTag.objects.filter(tenant=tenant)
    return Response(DocumentTagSerializer(tags, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def tag_create(request):
    """Create a document tag."""
    serializer = DocumentTagSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    tenant = getattr(request, 'tenant', None)
    serializer.save(tenant=tenant)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def seed_vault(request):
    """Trigger the document vault seed (admin only)."""
    from django.core.management import call_command
    from io import StringIO
    out = StringIO()
    err = StringIO()
    try:
        call_command('seed_document_vault', stdout=out, stderr=err)
        return Response({
            'status': 'ok',
            'stdout': out.getvalue(),
            'stderr': err.getvalue(),
            'total': Document.objects.count(),
        })
    except Exception as e:
        import traceback
        return Response({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc(),
            'stdout': out.getvalue(),
            'stderr': err.getvalue(),
        }, status=500)


def models_Q_valid(today):
    """Helper: Q filter for valid (non-expired, non-placeholder) documents."""
    from django.db.models import Q
    return (
        Q(expiry_date__isnull=True) | Q(expiry_date__gte=today)
    ) & (
        Q(is_placeholder=False) | Q(file__isnull=False)
    )
