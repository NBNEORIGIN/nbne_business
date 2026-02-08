from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from accounts.permissions import IsStaffOrAbove, IsManagerOrAbove
from .models import Document, DocumentTag
from .serializers import DocumentSerializer, DocumentCreateSerializer, DocumentTagSerializer


ROLE_HIERARCHY = {'customer': 0, 'staff': 1, 'manager': 2, 'owner': 3}


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def document_list(request):
    """List documents filtered by user's access tier."""
    docs = Document.objects.filter(is_active=True).select_related('uploaded_by').prefetch_related('tags')
    user_level = ROLE_HIERARCHY.get(request.user.role, 0)
    docs = [d for d in docs if ROLE_HIERARCHY.get(d.tier_access, 0) <= user_level]
    return Response(DocumentSerializer(docs, many=True).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def document_create(request):
    """Upload a document (manager+)."""
    serializer = DocumentCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    doc = serializer.save(uploaded_by=request.user)
    return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def document_detail(request, doc_id):
    try:
        doc = Document.objects.prefetch_related('tags').get(id=doc_id, is_active=True)
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
    user_level = ROLE_HIERARCHY.get(request.user.role, 0)
    if ROLE_HIERARCHY.get(doc.tier_access, 0) > user_level:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    return Response(DocumentSerializer(doc).data)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def expiry_reminders(request):
    """List documents expiring within 30 days."""
    today = timezone.now().date()
    from datetime import timedelta
    threshold = today + timedelta(days=30)
    docs = Document.objects.filter(
        is_active=True, expiry_date__isnull=False,
        expiry_date__lte=threshold,
    ).select_related('uploaded_by')
    return Response(DocumentSerializer(docs, many=True).data)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def tag_list(request):
    return Response(DocumentTagSerializer(DocumentTag.objects.all(), many=True).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def tag_create(request):
    name = request.data.get('name', '').strip()
    if not name:
        return Response({'error': 'name required'}, status=status.HTTP_400_BAD_REQUEST)
    tag, created = DocumentTag.objects.get_or_create(name=name)
    return Response(DocumentTagSerializer(tag).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
