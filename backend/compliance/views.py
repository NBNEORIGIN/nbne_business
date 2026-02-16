"""
Compliance Intelligence API views.
Provides Peace of Mind Score dashboard, compliance register CRUD,
calendar data, accident log, and priority actions.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
import calendar as cal_mod

from .models import (
    ComplianceItem, ComplianceCategory, PeaceOfMindScore,
    ScoreAuditLog, IncidentReport, Equipment, AccidentReport,
)


def _safe_date(val):
    """Ensure val is a string (isoformat) regardless of type."""
    if val is None:
        return None
    if isinstance(val, str):
        return val
    return val.isoformat()


def _serialize_item(item):
    """Serialize a ComplianceItem to dict."""
    return {
        'id': item.id,
        'title': item.title,
        'description': item.description,
        'category': item.category.name,
        'category_id': item.category_id,
        'item_type': item.item_type,
        'status': item.status,
        'frequency_type': item.frequency_type,
        'due_date': _safe_date(item.due_date),
        'next_due_date': _safe_date(item.next_due_date),
        'last_completed_date': _safe_date(item.last_completed_date),
        'completed_at': _safe_date(item.completed_at),
        'completed_by': item.completed_by,
        'regulatory_ref': item.regulatory_ref,
        'legal_reference': item.legal_reference,
        'evidence_required': item.evidence_required,
        'document': item.document.url if item.document else None,
        'notes': item.notes,
        'weight': item.weight,
        'created_at': item.created_at.isoformat(),
    }


def _serialize_accident(a):
    """Serialize an AccidentReport to dict."""
    return {
        'id': a.id,
        'date': _safe_date(a.date),
        'time': a.time.strftime('%H:%M') if a.time else None,
        'location': a.location,
        'person_involved': a.person_involved,
        'person_role': a.person_role,
        'description': a.description,
        'severity': a.severity,
        'status': a.status,
        'riddor_reportable': a.riddor_reportable,
        'hse_reference': a.hse_reference,
        'riddor_reported_date': _safe_date(a.riddor_reported_date),
        'follow_up_required': a.follow_up_required,
        'follow_up_notes': a.follow_up_notes,
        'follow_up_completed': a.follow_up_completed,
        'follow_up_completed_date': _safe_date(a.follow_up_completed_date),
        'document': a.document.url if a.document else None,
        'reported_by': a.reported_by,
        'created_at': a.created_at.isoformat(),
    }


# ========== DASHBOARD ==========

@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard(request):
    """
    GET /api/compliance/dashboard/
    """
    tenant = getattr(request, 'tenant', None)
    score_obj = PeaceOfMindScore.objects.filter(tenant=tenant).first()
    if not score_obj:
        score_obj = PeaceOfMindScore.recalculate()

    change_message = None
    change = score_obj.score_change
    if change > 0:
        change_message = f"Compliance improved by {change}% since last update."
    elif change < 0:
        overdue_count = score_obj.overdue_count
        if overdue_count > 0:
            change_message = f"{overdue_count} item{'s' if overdue_count != 1 else ''} became overdue."
        else:
            change_message = f"Score decreased by {abs(change)}%."

    open_incidents = IncidentReport.objects.filter(tenant=tenant).exclude(status__in=['RESOLVED', 'CLOSED']).count()
    today = timezone.now().date()
    overdue_equipment = Equipment.objects.filter(
        tenant=tenant, next_inspection__lt=today
    ).exclude(status='OUT_OF_SERVICE').count()

    # Accident counts
    open_accidents = AccidentReport.objects.filter(tenant=tenant).exclude(status='CLOSED').count()
    riddor_count = AccidentReport.objects.filter(tenant=tenant, riddor_reportable=True).count()

    return Response({
        'score': score_obj.score,
        'previous_score': score_obj.previous_score,
        'colour': score_obj.colour,
        'interpretation': score_obj.interpretation,
        'change_message': change_message,
        'total_items': score_obj.total_items,
        'compliant_count': score_obj.compliant_count,
        'due_soon_count': score_obj.due_soon_count,
        'overdue_count': score_obj.overdue_count,
        'legal_items': score_obj.legal_items,
        'best_practice_items': score_obj.best_practice_items,
        'open_incidents': open_incidents,
        'overdue_equipment': overdue_equipment,
        'open_accidents': open_accidents,
        'riddor_count': riddor_count,
        'last_calculated_at': score_obj.last_calculated_at.isoformat(),
    })


# ========== COMPLIANCE REGISTER (CRUD) ==========

@api_view(['GET'])
@permission_classes([AllowAny])
def items_list(request):
    """
    GET /api/compliance/items/
    Optional filters: ?status=OVERDUE&type=LEGAL&category=Fire+Safety
    """
    tenant = getattr(request, 'tenant', None)
    qs = ComplianceItem.objects.select_related('category').filter(category__tenant=tenant)
    if request.query_params.get('status'):
        qs = qs.filter(status=request.query_params['status'])
    if request.query_params.get('type'):
        qs = qs.filter(item_type=request.query_params['type'])
    if request.query_params.get('category'):
        qs = qs.filter(category__name=request.query_params['category'])

    return Response([_serialize_item(i) for i in qs])


@api_view(['POST'])
@permission_classes([AllowAny])
def items_create(request):
    """
    POST /api/compliance/items/create/
    """
    d = request.data
    tenant = getattr(request, 'tenant', None)
    cat_name = d.get('category', '')
    cat, _ = ComplianceCategory.objects.get_or_create(tenant=tenant, name=cat_name, defaults={'max_score': 10})

    item = ComplianceItem.objects.create(
        title=d.get('title', ''),
        description=d.get('description', ''),
        category=cat,
        item_type=d.get('item_type', 'BEST_PRACTICE'),
        frequency_type=d.get('frequency_type', 'annual'),
        next_due_date=d.get('next_due_date') or None,
        evidence_required=d.get('evidence_required', False),
        regulatory_ref=d.get('regulatory_ref', ''),
        legal_reference=d.get('legal_reference', ''),
        notes=d.get('notes', ''),
    )
    return Response(_serialize_item(item), status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def items_detail(request, item_id):
    """GET /api/compliance/items/<id>/"""
    try:
        tenant = getattr(request, 'tenant', None)
        item = ComplianceItem.objects.select_related('category').get(id=item_id, category__tenant=tenant)
    except ComplianceItem.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(_serialize_item(item))


@api_view(['DELETE'])
@permission_classes([AllowAny])
def items_delete(request, item_id):
    """DELETE /api/compliance/items/<id>/delete/"""
    try:
        tenant = getattr(request, 'tenant', None)
        item = ComplianceItem.objects.get(id=item_id, category__tenant=tenant)
    except ComplianceItem.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    item.delete()
    return Response({'message': 'Deleted'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([AllowAny])
def mark_complete(request, item_id):
    """
    POST /api/compliance/items/<id>/complete/
    Accepts: completed_date, completed_by, comments, evidence (file)
    Auto-recalculates next_due_date based on frequency_type.
    """
    try:
        tenant = getattr(request, 'tenant', None)
        item = ComplianceItem.objects.get(id=item_id, category__tenant=tenant)
    except ComplianceItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

    completed_date_str = request.data.get('completed_date')
    if completed_date_str:
        from datetime import date as dt_date
        try:
            parts = completed_date_str.split('-')
            completed_date = dt_date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            completed_date = timezone.now().date()
    else:
        completed_date = timezone.now().date()

    item.status = 'COMPLIANT'
    item.completed_at = timezone.now()
    item.last_completed_date = completed_date
    item.completed_by = request.data.get('completed_by', '')
    if request.data.get('comments'):
        item.notes = request.data['comments']

    # Handle evidence file upload
    if request.FILES.get('evidence'):
        item.document = request.FILES['evidence']

    # Auto-recalculate next_due_date
    new_due = item.compute_next_due()
    if new_due:
        item.next_due_date = new_due

    item.save()

    return Response({
        'id': item.id,
        'title': item.title,
        'status': 'COMPLIANT',
        'next_due_date': _safe_date(item.next_due_date),
        'last_completed_date': _safe_date(item.last_completed_date),
        'completed_by': item.completed_by,
        'document': item.document.url if item.document else None,
        'message': f'"{item.title}" marked as compliant. Next due: {item.next_due_date}',
    })


# ========== CALENDAR ==========

@api_view(['GET'])
@permission_classes([AllowAny])
def calendar_data(request):
    """
    GET /api/compliance/calendar/?year=2026&month=2
    Returns items grouped by date for the given month.
    """
    today = timezone.now().date()
    year = int(request.query_params.get('year', today.year))
    month = int(request.query_params.get('month', today.month))

    first_day = today.replace(year=year, month=month, day=1)
    _, last_day_num = cal_mod.monthrange(year, month)
    last_day = first_day.replace(day=last_day_num)

    tenant = getattr(request, 'tenant', None)
    items = ComplianceItem.objects.select_related('category').filter(
        category__tenant=tenant,
        next_due_date__gte=first_day,
        next_due_date__lte=last_day,
    )

    # Group by date
    days = {}
    for item in items:
        d = item.next_due_date.isoformat()
        if d not in days:
            days[d] = []
        colour = 'red' if item.status == 'OVERDUE' else ('amber' if item.status == 'DUE_SOON' else 'green')
        days[d].append({
            'id': item.id,
            'title': item.title,
            'item_type': item.item_type,
            'status': item.status,
            'colour': colour,
            'category': item.category.name,
        })

    return Response({
        'year': year,
        'month': month,
        'days': days,
    })


# ========== ACCIDENT LOG ==========

@api_view(['GET'])
@permission_classes([AllowAny])
def accidents_list(request):
    """GET /api/compliance/accidents/"""
    tenant = getattr(request, 'tenant', None)
    qs = AccidentReport.objects.filter(tenant=tenant)
    if request.query_params.get('status'):
        qs = qs.filter(status=request.query_params['status'])
    if request.query_params.get('riddor'):
        qs = qs.filter(riddor_reportable=True)
    return Response([_serialize_accident(a) for a in qs])


@api_view(['POST'])
@permission_classes([AllowAny])
def accidents_create(request):
    """POST /api/compliance/accidents/create/"""
    d = request.data
    time_val = None
    if d.get('time'):
        from datetime import time as dt_time
        parts = d['time'].split(':')
        time_val = dt_time(int(parts[0]), int(parts[1]))

    tenant = getattr(request, 'tenant', None)
    a = AccidentReport.objects.create(
        tenant=tenant,
        date=d.get('date'),
        time=time_val,
        location=d.get('location', ''),
        person_involved=d.get('person_involved', ''),
        person_role=d.get('person_role', ''),
        description=d.get('description', ''),
        severity=d.get('severity', 'MINOR'),
        riddor_reportable=d.get('riddor_reportable', False),
        hse_reference=d.get('hse_reference', ''),
        follow_up_required=d.get('follow_up_required', False),
        reported_by=d.get('reported_by', ''),
    )
    if request.FILES.get('document'):
        a.document = request.FILES['document']
        a.save()
    return Response(_serialize_accident(a), status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def accidents_delete(request, accident_id):
    """DELETE /api/compliance/accidents/<id>/delete/"""
    try:
        tenant = getattr(request, 'tenant', None)
        a = AccidentReport.objects.get(id=accident_id, tenant=tenant)
    except AccidentReport.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    a.delete()
    return Response({'message': 'Deleted'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['PATCH'])
@permission_classes([AllowAny])
def accidents_update(request, accident_id):
    """PATCH /api/compliance/accidents/<id>/update/"""
    try:
        tenant = getattr(request, 'tenant', None)
        a = AccidentReport.objects.get(id=accident_id, tenant=tenant)
    except AccidentReport.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    d = request.data
    for field in ['status', 'severity', 'hse_reference', 'riddor_reported_date',
                   'follow_up_notes', 'follow_up_completed', 'follow_up_completed_date',
                   'riddor_reportable', 'description', 'location']:
        if field in d:
            setattr(a, field, d[field])
    if request.FILES.get('document'):
        a.document = request.FILES['document']
    a.save()
    return Response(_serialize_accident(a))


# ========== EXISTING ENDPOINTS (preserved) ==========

@api_view(['GET'])
@permission_classes([AllowAny])
def breakdown(request):
    """GET /api/compliance/breakdown/"""
    item_type_filter = request.query_params.get('type')
    tenant = getattr(request, 'tenant', None)
    categories = ComplianceCategory.objects.filter(tenant=tenant)
    result = []

    for cat in categories:
        items = cat.items.all()
        if item_type_filter:
            items = items.filter(item_type=item_type_filter)
        total = items.count()
        if total == 0:
            continue
        compliant = items.filter(status='COMPLIANT').count()
        due_soon = items.filter(status='DUE_SOON').count()
        overdue = items.filter(status='OVERDUE').count()
        cat_total_weight = sum(i.weight for i in items)
        cat_achieved = sum(i.achieved_weight for i in items)
        cat_pct = round((cat_achieved / cat_total_weight) * 100) if cat_total_weight > 0 else 100

        result.append({
            'category': cat.name,
            'total_items': total,
            'compliant': compliant,
            'due_soon': due_soon,
            'overdue': overdue,
            'score_pct': cat_pct,
            'max_score': cat.max_score,
            'current_score': cat.current_score,
        })

    return Response({'categories': result, 'filter': item_type_filter or 'all'})


@api_view(['GET'])
@permission_classes([AllowAny])
def priority_actions(request):
    """GET /api/compliance/priorities/"""
    tenant = getattr(request, 'tenant', None)
    overdue_legal = ComplianceItem.objects.filter(category__tenant=tenant, status='OVERDUE', item_type='LEGAL').order_by('due_date')
    overdue_bp = ComplianceItem.objects.filter(category__tenant=tenant, status='OVERDUE', item_type='BEST_PRACTICE').order_by('due_date')
    due_soon_legal = ComplianceItem.objects.filter(category__tenant=tenant, status='DUE_SOON', item_type='LEGAL').order_by('due_date')
    due_soon_bp = ComplianceItem.objects.filter(category__tenant=tenant, status='DUE_SOON', item_type='BEST_PRACTICE').order_by('due_date')

    combined = list(overdue_legal) + list(overdue_bp) + list(due_soon_legal) + list(due_soon_bp)
    top_items = combined[:10]

    actions = []
    for item in top_items:
        actions.append({
            'id': item.id,
            'title': item.title,
            'category': item.category.name,
            'item_type': item.item_type,
            'status': item.status,
            'due_date': item.due_date.isoformat() if item.due_date else None,
            'next_due_date': item.next_due_date.isoformat() if item.next_due_date else None,
            'regulatory_ref': item.regulatory_ref,
            'legal_reference': item.legal_reference,
            'frequency_type': item.frequency_type,
            'evidence_required': item.evidence_required,
            'weight': item.weight,
        })

    return Response({'actions': actions})


@api_view(['GET'])
@permission_classes([AllowAny])
def categories_list(request):
    """GET /api/compliance/categories/"""
    tenant = getattr(request, 'tenant', None)
    cats = ComplianceCategory.objects.filter(tenant=tenant)
    return Response([
        {'id': c.id, 'name': c.name, 'max_score': c.max_score, 'current_score': c.current_score}
        for c in cats
    ])


@api_view(['GET'])
@permission_classes([AllowAny])
def audit_log(request):
    """GET /api/compliance/audit-log/"""
    limit = int(request.query_params.get('limit', 20))
    logs = ScoreAuditLog.objects.all()[:limit]
    return Response({
        'logs': [
            {
                'score': log.score,
                'previous_score': log.previous_score,
                'change': log.score - log.previous_score,
                'total_items': log.total_items,
                'compliant_count': log.compliant_count,
                'due_soon_count': log.due_soon_count,
                'overdue_count': log.overdue_count,
                'trigger': log.get_trigger_display(),
                'calculated_at': log.calculated_at.isoformat(),
            }
            for log in logs
        ]
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def recalculate(request):
    """POST /api/compliance/recalculate/"""
    result = PeaceOfMindScore.recalculate()
    latest_log = ScoreAuditLog.objects.order_by('-calculated_at').first()
    if latest_log:
        latest_log.trigger = 'manual'
        latest_log.save(update_fields=['trigger'])
    return Response({
        'score': result.score,
        'previous_score': result.previous_score,
        'message': f'Score recalculated: {result.score}%',
    })


# ========== VISUAL DASHBOARD V2 ENDPOINTS ==========

@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_v2(request):
    """
    GET /api/compliance/dashboard-v2/
    Enhanced dashboard with time horizon, trend, priority scoring.
    """
    tenant = getattr(request, 'tenant', None)
    score_obj = PeaceOfMindScore.objects.filter(tenant=tenant).first()
    if not score_obj:
        score_obj = PeaceOfMindScore.recalculate()

    today = timezone.now().date()

    # --- Time horizon buckets ---
    items = list(ComplianceItem.objects.select_related('category').filter(category__tenant=tenant))

    horizon = {'next_7': [], 'next_30': [], 'next_90': [], 'overdue': []}
    for item in items:
        due = item.next_due_date
        if not due:
            continue
        if due < today:
            horizon['overdue'].append(_serialize_item(item))
        elif due <= today + timedelta(days=7):
            horizon['next_7'].append(_serialize_item(item))
        elif due <= today + timedelta(days=30):
            horizon['next_30'].append(_serialize_item(item))
        elif due <= today + timedelta(days=90):
            horizon['next_90'].append(_serialize_item(item))

    # --- Priority scoring ---
    priority_items = []
    for item in items:
        p_score = 0
        due = item.next_due_date
        if item.item_type == 'LEGAL' and item.status == 'OVERDUE':
            p_score += 50
        elif item.item_type == 'LEGAL' and due and due <= today + timedelta(days=14):
            p_score += 30
        elif item.item_type == 'BEST_PRACTICE' and item.status == 'OVERDUE':
            p_score += 20
        elif item.item_type == 'BEST_PRACTICE' and due and due <= today + timedelta(days=30):
            p_score += 10

        if p_score > 0 or item.status != 'COMPLIANT':
            level = 'high' if p_score >= 30 else ('medium' if p_score >= 10 else 'low')
            serialized = _serialize_item(item)
            serialized['priority_score'] = p_score
            serialized['priority_level'] = level
            priority_items.append(serialized)

    priority_items.sort(key=lambda x: -x['priority_score'])

    # --- Trend data (last 30 days from audit log) ---
    thirty_days_ago = timezone.now() - timedelta(days=30)
    logs = ScoreAuditLog.objects.filter(
        calculated_at__gte=thirty_days_ago
    ).order_by('calculated_at')
    trend = [{
        'date': log.calculated_at.isoformat(),
        'score': log.score,
        'trigger': log.get_trigger_display(),
        'change': log.score - log.previous_score,
    } for log in logs]

    # --- Dynamic summary text ---
    summary_parts = []
    if score_obj.score >= 80:
        summary_parts.append("You are fully compliant.")
    overdue_legal = ComplianceItem.objects.filter(category__tenant=tenant, status='OVERDUE', item_type='LEGAL').count()
    if overdue_legal > 0:
        summary_parts.append(f"{overdue_legal} legal item{'s' if overdue_legal != 1 else ''} overdue — immediate action required.")
    due_14 = ComplianceItem.objects.filter(
        category__tenant=tenant, status='DUE_SOON', item_type='LEGAL',
        next_due_date__lte=today + timedelta(days=14)
    ).count()
    if due_14 > 0:
        summary_parts.append(f"{due_14} legal item{'s' if due_14 != 1 else ''} due within 14 days.")
    if not summary_parts:
        summary_parts.append(score_obj.interpretation)

    # Accident stats
    open_accidents = AccidentReport.objects.filter(tenant=tenant).exclude(status='CLOSED').count()
    riddor_count = AccidentReport.objects.filter(tenant=tenant, riddor_reportable=True).count()

    return Response({
        'score': score_obj.score,
        'previous_score': score_obj.previous_score,
        'colour': score_obj.colour,
        'interpretation': score_obj.interpretation,
        'summary_text': ' '.join(summary_parts),
        'total_items': score_obj.total_items,
        'compliant_count': score_obj.compliant_count,
        'due_soon_count': score_obj.due_soon_count,
        'overdue_count': score_obj.overdue_count,
        'legal_items': score_obj.legal_items,
        'best_practice_items': score_obj.best_practice_items,
        'time_horizon': {
            'overdue': len(horizon['overdue']),
            'next_7': len(horizon['next_7']),
            'next_30': len(horizon['next_30']),
            'next_90': len(horizon['next_90']),
            'overdue_items': horizon['overdue'],
            'next_7_items': horizon['next_7'],
            'next_30_items': horizon['next_30'],
            'next_90_items': horizon['next_90'],
        },
        'trend': trend,
        'priority_items': priority_items,
        'open_accidents': open_accidents,
        'riddor_count': riddor_count,
    })
