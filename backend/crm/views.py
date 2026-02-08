import csv
from io import StringIO
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.utils import timezone
from accounts.permissions import IsManagerOrAbove
from .models import Lead, LeadNote, FollowUp
from .serializers import (
    LeadSerializer, LeadCreateSerializer, LeadStatusSerializer,
    NoteCreateSerializer, FollowUpCreateSerializer, FollowUpSerializer,
)


@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def lead_list(request):
    """List leads (manager+). Supports ?status= and ?source= filters."""
    leads = Lead.objects.select_related('assigned_to', 'created_by').prefetch_related('lead_notes', 'follow_ups').all()
    s = request.query_params.get('status')
    if s:
        leads = leads.filter(status=s)
    src = request.query_params.get('source')
    if src:
        leads = leads.filter(source=src)
    return Response(LeadSerializer(leads, many=True).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def lead_create(request):
    """Create a lead (manager+)."""
    serializer = LeadCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    lead = serializer.save(created_by=request.user)
    return Response(LeadSerializer(lead).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def lead_detail(request, lead_id):
    try:
        lead = Lead.objects.prefetch_related('lead_notes', 'follow_ups').get(id=lead_id)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(LeadSerializer(lead).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def lead_update_status(request, lead_id):
    """Update lead status (manager+)."""
    try:
        lead = Lead.objects.get(id=lead_id)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = LeadStatusSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    lead.status = serializer.validated_data['status']
    lead.save(update_fields=['status', 'updated_at'])
    return Response(LeadSerializer(lead).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def note_create(request, lead_id):
    """Add a note to a lead (manager+)."""
    try:
        lead = Lead.objects.get(id=lead_id)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = NoteCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    LeadNote.objects.create(lead=lead, author=request.user, body=serializer.validated_data['body'])
    return Response(LeadSerializer(lead).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def follow_up_create(request, lead_id):
    """Create a follow-up for a lead (manager+)."""
    try:
        lead = Lead.objects.get(id=lead_id)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = FollowUpCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    fu = serializer.save(lead=lead)
    return Response(FollowUpSerializer(fu).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def follow_up_complete(request, follow_up_id):
    """Mark a follow-up as completed (manager+)."""
    try:
        fu = FollowUp.objects.get(id=follow_up_id)
    except FollowUp.DoesNotExist:
        return Response({'error': 'Follow-up not found'}, status=status.HTTP_404_NOT_FOUND)
    fu.is_completed = True
    fu.completed_at = timezone.now()
    fu.save(update_fields=['is_completed', 'completed_at'])
    return Response(FollowUpSerializer(fu).data)


@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def lead_export_csv(request):
    """Export leads as CSV (manager+)."""
    leads = Lead.objects.all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Email', 'Phone', 'Source', 'Status', 'Value (pence)', 'Created'])
    for lead in leads:
        writer.writerow([lead.name, lead.email, lead.phone, lead.source, lead.status, lead.value_pence, lead.created_at.isoformat()])
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="leads_export.csv"'
    return response
