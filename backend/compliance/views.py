import csv
import io
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from accounts.permissions import IsStaffOrAbove, IsManagerOrAbove
from .models import (
    ComplianceCategory, ComplianceItem, IncidentReport, IncidentPhoto,
    SignOff, TrainingRecord, DocumentVault, ComplianceActionLog, RAMSDocument,
)
from .serializers import (
    ComplianceCategorySerializer, ComplianceCategoryCreateSerializer,
    ComplianceItemSerializer, ComplianceItemCreateSerializer, ComplianceItemCompleteSerializer,
    IncidentReportSerializer, IncidentCreateSerializer, IncidentStatusSerializer,
    SignOffCreateSerializer, TrainingRecordSerializer, TrainingRecordCreateSerializer,
    DocumentVaultSerializer, DocumentVaultCreateSerializer,
    ComplianceActionLogSerializer, RAMSDocumentSerializer, RAMSCreateSerializer,
)


# ===========================================================================
# TIER 3: Compliance Dashboard
# ===========================================================================
@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def compliance_dashboard(request):
    """Compliance overview dashboard with RAG indicators."""
    today = timezone.now().date()
    items = ComplianceItem.objects.all()
    total = items.count()
    compliant = items.filter(status='compliant').count()
    due_soon = items.filter(status='due_soon').count()
    overdue = items.filter(status='overdue').count()
    not_started = items.filter(status='not_started').count()

    # Training summary
    training = TrainingRecord.objects.all()
    expired_training = training.filter(expiry_date__lt=today).count()
    expiring_training = training.filter(expiry_date__gte=today, expiry_date__lte=today + timedelta(days=30)).count()

    # Incident summary
    open_incidents = IncidentReport.objects.exclude(status__in=['RESOLVED', 'CLOSED']).count()
    riddor_count = IncidentReport.objects.filter(riddor_reportable=True).count()

    # Document summary
    expired_docs = DocumentVault.objects.filter(is_current=True, expiry_date__lt=today).count()

    # Category breakdown
    categories = ComplianceCategory.objects.prefetch_related('items').all()
    cat_breakdown = []
    for cat in categories:
        cat_items = cat.items.all()
        cat_total = cat_items.count()
        if cat_total == 0:
            continue
        cat_overdue = cat_items.filter(status='overdue').count()
        cat_due_soon = cat_items.filter(status='due_soon').count()
        cat_compliant = cat_items.filter(status='compliant').count()
        pct = round((cat_compliant / cat_total) * 100) if cat_total > 0 else 0
        cat_breakdown.append({
            'id': cat.id,
            'name': cat.name,
            'legal_requirement': cat.legal_requirement,
            'total': cat_total,
            'compliant': cat_compliant,
            'due_soon': cat_due_soon,
            'overdue': cat_overdue,
            'score_pct': pct,
        })

    # Overall score
    score_pct = round((compliant / total) * 100) if total > 0 else 100

    return Response({
        'score': score_pct,
        'total_items': total,
        'compliant': compliant,
        'due_soon': due_soon,
        'overdue': overdue,
        'not_started': not_started,
        'expired_training': expired_training,
        'expiring_training': expiring_training,
        'open_incidents': open_incidents,
        'riddor_count': riddor_count,
        'expired_documents': expired_docs,
        'categories': cat_breakdown,
    })


# ===========================================================================
# TIER 3: Calendar feed — all upcoming due dates
# ===========================================================================
@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def calendar_feed(request):
    """Return compliance items and training as calendar events."""
    today = timezone.now().date()
    lookahead = int(request.query_params.get('days', 90))
    end_date = today + timedelta(days=lookahead)

    events = []

    # Compliance items with due dates
    items = ComplianceItem.objects.filter(
        next_due_date__gte=today, next_due_date__lte=end_date,
    ).select_related('category', 'responsible_user')
    for item in items:
        events.append({
            'id': f'item-{item.id}',
            'type': 'compliance_item',
            'title': item.title,
            'date': item.next_due_date.isoformat(),
            'status': item.status,
            'category': item.category.name,
            'legal': item.category.legal_requirement,
            'responsible': item.responsible_user.get_full_name() if item.responsible_user else None,
        })

    # Training expiry dates
    training = TrainingRecord.objects.filter(
        expiry_date__gte=today, expiry_date__lte=end_date,
    ).select_related('user')
    for tr in training:
        events.append({
            'id': f'training-{tr.id}',
            'type': 'training_expiry',
            'title': f"{tr.get_training_type_display()} — {tr.user.get_full_name()}",
            'date': tr.expiry_date.isoformat(),
            'status': tr.status,
            'user': tr.user.get_full_name(),
        })

    # Document expiry dates
    docs = DocumentVault.objects.filter(
        is_current=True, expiry_date__gte=today, expiry_date__lte=end_date,
    )
    for doc in docs:
        events.append({
            'id': f'doc-{doc.id}',
            'type': 'document_expiry',
            'title': f"Doc: {doc.title} v{doc.version}",
            'date': doc.expiry_date.isoformat(),
            'status': 'expired' if doc.is_expired else 'valid',
        })

    # Overdue items (past due)
    overdue_items = ComplianceItem.objects.filter(status='overdue').select_related('category')
    for item in overdue_items:
        if item.next_due_date and item.next_due_date < today:
            events.append({
                'id': f'overdue-{item.id}',
                'type': 'overdue',
                'title': f"OVERDUE: {item.title}",
                'date': item.next_due_date.isoformat(),
                'status': 'overdue',
                'category': item.category.name,
                'legal': item.category.legal_requirement,
            })

    events.sort(key=lambda e: e['date'])
    return Response({'events': events, 'from': today.isoformat(), 'to': end_date.isoformat()})


# ===========================================================================
# TIER 3: CSV Export
# ===========================================================================
@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def export_csv(request):
    """Export compliance register as CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="compliance_register_{timezone.now().date()}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Category', 'Legal Requirement', 'Item', 'Status', 'Frequency',
        'Last Completed', 'Next Due', 'Responsible', 'Baseline', 'Notes',
    ])

    items = ComplianceItem.objects.select_related('category', 'responsible_user').all()
    for item in items:
        writer.writerow([
            item.category.name,
            'Yes' if item.category.legal_requirement else 'No',
            item.title,
            item.get_status_display(),
            item.get_frequency_type_display(),
            item.last_completed_date or '',
            item.next_due_date or '',
            item.responsible_user.get_full_name() if item.responsible_user else '',
            'Yes' if item.is_baseline else 'No',
            item.notes,
        ])

    return response


# ===========================================================================
# TIER 3: ComplianceCategory CRUD
# ===========================================================================
@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def category_list(request):
    """List all compliance categories."""
    cats = ComplianceCategory.objects.prefetch_related('items').all()
    return Response(ComplianceCategorySerializer(cats, many=True).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def category_create(request):
    """Create a compliance category."""
    serializer = ComplianceCategoryCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    cat = serializer.save()
    return Response(ComplianceCategorySerializer(cat).data, status=status.HTTP_201_CREATED)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsManagerOrAbove])
def category_detail(request, category_id):
    """Update or delete a compliance category."""
    try:
        cat = ComplianceCategory.objects.get(id=category_id)
    except ComplianceCategory.DoesNotExist:
        return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        cat.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ComplianceCategoryCreateSerializer(cat, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(ComplianceCategorySerializer(cat).data)


# ===========================================================================
# TIER 3: ComplianceItem CRUD
# ===========================================================================
@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def item_list(request):
    """List compliance items. Supports ?status=, ?category=, ?legal= filters."""
    items = ComplianceItem.objects.select_related('category', 'responsible_user').all()
    s = request.query_params.get('status')
    if s:
        items = items.filter(status=s)
    cat = request.query_params.get('category')
    if cat:
        items = items.filter(category_id=cat)
    legal = request.query_params.get('legal')
    if legal == 'true':
        items = items.filter(category__legal_requirement=True)
    return Response(ComplianceItemSerializer(items, many=True).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def item_create(request):
    """Create a compliance item."""
    serializer = ComplianceItemCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    item = serializer.save()
    ComplianceActionLog.objects.create(
        compliance_item=item, action='created', user=request.user,
        notes=f'Created: {item.title}',
    )
    return Response(ComplianceItemSerializer(item).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsManagerOrAbove])
def item_detail(request, item_id):
    """Get, update, or delete a compliance item."""
    try:
        item = ComplianceItem.objects.select_related('category', 'responsible_user').get(id=item_id)
    except ComplianceItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(ComplianceItemSerializer(item).data)

    if request.method == 'DELETE':
        ComplianceActionLog.objects.create(
            action='updated', user=request.user,
            notes=f'Deleted item: {item.title}',
        )
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ComplianceItemCreateSerializer(item, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    old_status = item.status
    serializer.save()
    if item.status != old_status:
        ComplianceActionLog.objects.create(
            compliance_item=item, action='status_change', user=request.user,
            notes=f'Status: {old_status} → {item.status}',
        )
    else:
        ComplianceActionLog.objects.create(
            compliance_item=item, action='updated', user=request.user,
            notes=f'Updated: {item.title}',
        )
    return Response(ComplianceItemSerializer(item).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def item_complete(request, item_id):
    """Mark a compliance item as completed and recalculate next due date."""
    try:
        item = ComplianceItem.objects.get(id=item_id)
    except ComplianceItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ComplianceItemCompleteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    completed_date = serializer.validated_data.get('completed_date')
    item.mark_completed(completed_date=completed_date)

    ComplianceActionLog.objects.create(
        compliance_item=item, action='completed', user=request.user,
        notes=f'Completed on {item.last_completed_date}. Next due: {item.next_due_date}',
    )
    return Response(ComplianceItemSerializer(item).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def item_assign(request, item_id):
    """Assign a compliance item to a user."""
    try:
        item = ComplianceItem.objects.get(id=item_id)
    except ComplianceItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

    user_id = request.data.get('user_id')
    if not user_id:
        return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)

    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        assignee = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    item.responsible_user = assignee
    item.save(update_fields=['responsible_user', 'updated_at'])

    ComplianceActionLog.objects.create(
        compliance_item=item, action='assigned', user=request.user,
        notes=f'Assigned to {assignee.get_full_name()}',
    )
    return Response(ComplianceItemSerializer(item).data)


# ===========================================================================
# TIER 2: My Actions (staff sees their assigned items)
# ===========================================================================
@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def my_actions(request):
    """Return compliance items assigned to the current user."""
    items = ComplianceItem.objects.filter(
        responsible_user=request.user,
    ).select_related('category').exclude(status='compliant')
    return Response(ComplianceItemSerializer(items, many=True).data)


# ===========================================================================
# TIER 2: My Training
# ===========================================================================
@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def my_training(request):
    """Return training records for the current user."""
    records = TrainingRecord.objects.filter(user=request.user)
    return Response(TrainingRecordSerializer(records, many=True).data)


# ===========================================================================
# TIER 3: Training CRUD
# ===========================================================================
@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def training_list(request):
    """List all training records. Supports ?user=, ?type=, ?status= filters."""
    records = TrainingRecord.objects.select_related('user').all()
    user_id = request.query_params.get('user')
    if user_id:
        records = records.filter(user_id=user_id)
    tr_type = request.query_params.get('type')
    if tr_type:
        records = records.filter(training_type=tr_type)
    tr_status = request.query_params.get('status')
    if tr_status == 'expired':
        records = records.filter(expiry_date__lt=timezone.now().date())
    elif tr_status == 'expiring_soon':
        today = timezone.now().date()
        records = records.filter(expiry_date__gte=today, expiry_date__lte=today + timedelta(days=30))
    elif tr_status == 'valid':
        records = records.filter(Q(expiry_date__gt=timezone.now().date() + timedelta(days=30)) | Q(expiry_date__isnull=True))
    return Response(TrainingRecordSerializer(records, many=True).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def training_create(request):
    """Create a training record."""
    serializer = TrainingRecordCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    record = serializer.save()
    ComplianceActionLog.objects.create(
        action='created', user=request.user,
        notes=f'Training record: {record.get_training_type_display()} for {record.user.get_full_name()}',
    )
    return Response(TrainingRecordSerializer(record).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsManagerOrAbove])
def training_detail(request, training_id):
    """Get, update, or delete a training record."""
    try:
        record = TrainingRecord.objects.select_related('user').get(id=training_id)
    except TrainingRecord.DoesNotExist:
        return Response({'error': 'Training record not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(TrainingRecordSerializer(record).data)

    if request.method == 'DELETE':
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = TrainingRecordCreateSerializer(record, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(TrainingRecordSerializer(record).data)


# ===========================================================================
# TIER 3: Document Vault
# ===========================================================================
@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def document_list(request):
    """List current documents. Supports ?type= filter."""
    docs = DocumentVault.objects.filter(is_current=True).select_related('uploaded_by')
    doc_type = request.query_params.get('type')
    if doc_type:
        docs = docs.filter(document_type=doc_type)
    return Response(DocumentVaultSerializer(docs, many=True).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def document_upload(request):
    """Upload a new document."""
    serializer = DocumentVaultCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    doc = serializer.save(uploaded_by=request.user)
    ComplianceActionLog.objects.create(
        action='document_uploaded', user=request.user,
        notes=f'Uploaded: {doc.title} v{doc.version}',
    )
    return Response(DocumentVaultSerializer(doc).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'DELETE'])
@permission_classes([IsManagerOrAbove])
def document_detail(request, doc_id):
    """Get or delete a document."""
    try:
        doc = DocumentVault.objects.get(id=doc_id)
    except DocumentVault.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(DocumentVaultSerializer(doc).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def document_new_version(request, doc_id):
    """Upload a new version of an existing document."""
    try:
        doc = DocumentVault.objects.get(id=doc_id)
    except DocumentVault.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

    file = request.FILES.get('file')
    if not file:
        return Response({'error': 'file is required'}, status=status.HTTP_400_BAD_REQUEST)

    new_version = request.data.get('version')
    new_doc = doc.upload_new_version(file=file, uploaded_by=request.user, new_version=new_version)

    ComplianceActionLog.objects.create(
        action='document_uploaded', user=request.user,
        notes=f'New version: {new_doc.title} v{new_doc.version} (supersedes v{doc.version})',
    )
    return Response(DocumentVaultSerializer(new_doc).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def document_versions(request, doc_id):
    """List all versions of a document."""
    try:
        doc = DocumentVault.objects.get(id=doc_id)
    except DocumentVault.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

    # Walk the chain
    versions = [doc]
    current = doc
    while current.supersedes:
        versions.append(current.supersedes)
        current = current.supersedes
    versions.reverse()
    return Response(DocumentVaultSerializer(versions, many=True).data)


# ===========================================================================
# TIER 3: Action Logs
# ===========================================================================
@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def action_log_list(request):
    """List compliance action logs. Supports ?item=, ?incident=, ?limit= filters."""
    logs = ComplianceActionLog.objects.select_related('user', 'compliance_item', 'incident').all()
    item_id = request.query_params.get('item')
    if item_id:
        logs = logs.filter(compliance_item_id=item_id)
    incident_id = request.query_params.get('incident')
    if incident_id:
        logs = logs.filter(incident_id=incident_id)
    limit = int(request.query_params.get('limit', 50))
    return Response(ComplianceActionLogSerializer(logs[:limit], many=True).data)


# ===========================================================================
# TIER 2: Incidents (preserved + enhanced)
# ===========================================================================
@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def incident_list(request):
    """List incidents (staff+). Supports ?status= and ?severity= filters."""
    incidents = IncidentReport.objects.select_related('reported_by', 'assigned_to', 'reviewed_by').prefetch_related('photos', 'sign_offs').all()
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
    ComplianceActionLog.objects.create(
        incident=incident, action='created', user=request.user,
        notes=f'Incident reported: {incident.title}',
    )
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
@permission_classes([IsStaffOrAbove])
def incident_upload_photo(request, incident_id):
    """Upload a photo to an incident (staff+)."""
    try:
        incident = IncidentReport.objects.get(id=incident_id)
    except IncidentReport.DoesNotExist:
        return Response({'error': 'Incident not found'}, status=status.HTTP_404_NOT_FOUND)

    image = request.FILES.get('image')
    if not image:
        return Response({'error': 'image file is required'}, status=status.HTTP_400_BAD_REQUEST)

    caption = request.data.get('caption', '')
    photo = IncidentPhoto.objects.create(
        incident=incident, image=image, caption=caption, uploaded_by=request.user,
    )
    return Response({'id': photo.id, 'caption': photo.caption, 'uploaded_at': photo.uploaded_at}, status=status.HTTP_201_CREATED)


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
    old_status = incident.status
    incident.status = serializer.validated_data['status']
    if serializer.validated_data.get('resolution_notes'):
        incident.resolution_notes = serializer.validated_data['resolution_notes']
    if incident.status == 'RESOLVED':
        incident.resolved_at = timezone.now()
    incident.reviewed_by = request.user
    incident.save(update_fields=['status', 'resolution_notes', 'resolved_at', 'reviewed_by', 'updated_at'])
    ComplianceActionLog.objects.create(
        incident=incident, action='status_change', user=request.user,
        notes=f'Status: {old_status} → {incident.status}',
    )
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
    ComplianceActionLog.objects.create(
        incident=incident, action='reviewed', user=request.user,
        notes=f'Signed off by {request.user.get_full_name()}',
    )
    return Response(IncidentReportSerializer(incident).data)


# ===========================================================================
# TIER 2+: RAMS (preserved)
# ===========================================================================
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
