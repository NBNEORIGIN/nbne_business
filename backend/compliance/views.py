from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from accounts.permissions import IsStaffOrAbove, IsManagerOrAbove
from .models import IncidentReport, SignOff, RAMSDocument
from .serializers import (
    IncidentReportSerializer, IncidentCreateSerializer, IncidentStatusSerializer,
    SignOffCreateSerializer, RAMSDocumentSerializer, RAMSCreateSerializer,
)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def incident_list(request):
    """List incidents (staff+). Supports ?status= and ?severity= filters."""
    incidents = IncidentReport.objects.select_related('reported_by', 'assigned_to').prefetch_related('photos', 'sign_offs').all()
    s = request.query_params.get('status')
    if s:
        incidents = incidents.filter(status=s)
    sev = request.query_params.get('severity')
    if sev:
        incidents = incidents.filter(severity=sev)
    return Response(IncidentReportSerializer(incidents, many=True).data)


@api_view(['POST'])
@permission_classes([IsStaffOrAbove])
def incident_create(request):
    """Create an incident report (staff+)."""
    serializer = IncidentCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    incident = serializer.save(reported_by=request.user)
    return Response(IncidentReportSerializer(incident).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def incident_detail(request, incident_id):
    try:
        incident = IncidentReport.objects.prefetch_related('photos', 'sign_offs').get(id=incident_id)
    except IncidentReport.DoesNotExist:
        return Response({'error': 'Incident not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(IncidentReportSerializer(incident).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def incident_update_status(request, incident_id):
    """Update incident status (manager+)."""
    try:
        incident = IncidentReport.objects.get(id=incident_id)
    except IncidentReport.DoesNotExist:
        return Response({'error': 'Incident not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = IncidentStatusSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    incident.status = serializer.validated_data['status']
    if serializer.validated_data.get('resolution_notes'):
        incident.resolution_notes = serializer.validated_data['resolution_notes']
    if incident.status == 'RESOLVED':
        incident.resolved_at = timezone.now()
    incident.save(update_fields=['status', 'resolution_notes', 'resolved_at', 'updated_at'])
    return Response(IncidentReportSerializer(incident).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def incident_sign_off(request, incident_id):
    """Sign off on an incident (manager+)."""
    try:
        incident = IncidentReport.objects.get(id=incident_id)
    except IncidentReport.DoesNotExist:
        return Response({'error': 'Incident not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = SignOffCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    SignOff.objects.create(
        incident=incident, signed_by=request.user,
        role=request.user.role, notes=serializer.validated_data.get('notes', ''),
    )
    return Response(IncidentReportSerializer(incident).data)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def rams_list(request):
    """List RAMS documents (staff+)."""
    rams = RAMSDocument.objects.select_related('created_by').all()
    s = request.query_params.get('status')
    if s:
        rams = rams.filter(status=s)
    return Response(RAMSDocumentSerializer(rams, many=True).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def rams_create(request):
    """Create a RAMS document (manager+)."""
    serializer = RAMSCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    rams = serializer.save(created_by=request.user)
    return Response(RAMSDocumentSerializer(rams).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def rams_detail(request, rams_id):
    try:
        rams = RAMSDocument.objects.get(id=rams_id)
    except RAMSDocument.DoesNotExist:
        return Response({'error': 'RAMS not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(RAMSDocumentSerializer(rams).data)
