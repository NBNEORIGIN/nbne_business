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
    RAMSDocument,
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
        'expiry_date': _safe_date(getattr(item, 'expiry_date', None)),
        'reminder_days': getattr(item, 'reminder_days', 30),
        'last_completed_date': _safe_date(item.last_completed_date),
        'completed_at': _safe_date(item.completed_at),
        'completed_by': item.completed_by,
        'regulatory_ref': item.regulatory_ref,
        'legal_reference': item.legal_reference,
        'plain_english_why': getattr(item, 'plain_english_why', ''),
        'primary_action': getattr(item, 'primary_action', ''),
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
        score_obj = PeaceOfMindScore.recalculate(tenant=tenant)

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
    tenant = getattr(request, 'tenant', None)
    result = PeaceOfMindScore.recalculate(tenant=tenant)
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
        score_obj = PeaceOfMindScore.recalculate(tenant=tenant)

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


# ========== WIGGUM DASHBOARD ==========

def _action_label(item):
    """Return the primary action label for a compliance item."""
    pa = getattr(item, 'primary_action', '')
    if pa:
        return pa
    if item.evidence_required and not item.document:
        return 'Upload document'
    if item.status == 'OVERDUE':
        return 'Fix now'
    return 'Mark complete'


def _why_label(item):
    """Return plain-English why this matters."""
    pe = getattr(item, 'plain_english_why', '')
    if pe:
        return pe
    if item.item_type == 'LEGAL':
        return 'Required by law'
    return 'Best practice for your business'


@api_view(['GET'])
@permission_classes([AllowAny])
def wiggum(request):
    """
    GET /api/compliance/wiggum/
    Wiggum Loop dashboard — answers "Am I safe, or am I in trouble?"
    Returns: status_level, status_message, action_items[], sorted_items[], score
    """
    tenant = getattr(request, 'tenant', None)
    today = timezone.now().date()

    items = list(ComplianceItem.objects.select_related('category').filter(category__tenant=tenant))
    open_incidents = IncidentReport.objects.filter(tenant=tenant).exclude(status__in=['RESOLVED', 'CLOSED']).count()
    open_accidents = AccidentReport.objects.filter(tenant=tenant).exclude(status='CLOSED').count()

    # Categorise items
    overdue_legal = [i for i in items if i.status == 'OVERDUE' and i.item_type == 'LEGAL']
    overdue_bp = [i for i in items if i.status == 'OVERDUE' and i.item_type == 'BEST_PRACTICE']
    due_soon = [i for i in items if i.status == 'DUE_SOON']
    compliant = [i for i in items if i.status == 'COMPLIANT']
    missing = [i for i in items if not i.last_completed_date and not i.document and i.status == 'OVERDUE']

    # Determine status level
    needs_attention_count = len(overdue_bp) + len(due_soon)
    if overdue_legal or open_incidents > 0:
        status_level = 'red'
        if overdue_legal:
            status_message = f"You have legal risk. {len(overdue_legal)} legal item{'s' if len(overdue_legal) != 1 else ''} overdue. Fix today."
        else:
            status_message = f"You have {open_incidents} open incident{'s' if open_incidents != 1 else ''}. Resolve now."
    elif needs_attention_count > 0:
        status_level = 'amber'
        status_message = f"{needs_attention_count} thing{'s' if needs_attention_count != 1 else ''} need{'s' if needs_attention_count == 1 else ''} doing."
    else:
        status_level = 'green'
        status_message = "All sorted. Nothing urgent."

    # Build action table — ordered: overdue legal first, then overdue BP, then due soon
    action_items = []
    for item in overdue_legal + overdue_bp + due_soon:
        days_info = ''
        effective_date = item.expiry_date or item.next_due_date
        if effective_date:
            d = daysUntil_py(effective_date, today)
            if d < 0:
                days_info = f'{abs(d)} days overdue'
            elif d == 0:
                days_info = 'Due today'
            else:
                days_info = f'Due in {d} days'

        action_items.append({
            'id': item.id,
            'what': item.title,
            'why': _why_label(item),
            'do_this': _action_label(item),
            'status': item.status,
            'item_type': item.item_type,
            'days_info': days_info,
            'category': item.category.name,
            'has_document': bool(item.document),
            'plain_english_why': getattr(item, 'plain_english_why', ''),
            'description': item.description,
            'legal_reference': item.legal_reference,
        })

    # Sorted view — recently completed items
    week_ago = today - timedelta(days=7)
    completed_today = [i for i in items if i.last_completed_date and i.last_completed_date == today]
    completed_this_week = [i for i in items if i.last_completed_date and week_ago <= i.last_completed_date < today]

    sorted_items = []
    for item in completed_today:
        sorted_items.append({'id': item.id, 'title': item.title, 'when': 'today', 'category': item.category.name})
    for item in completed_this_week:
        sorted_items.append({'id': item.id, 'title': item.title, 'when': str(item.last_completed_date), 'category': item.category.name})

    # Score
    score_obj = PeaceOfMindScore.objects.filter(tenant=tenant).first()
    score = score_obj.score if score_obj else 0
    score_label = 'Safe' if status_level == 'green' else ('Attention needed' if status_level == 'amber' else 'Legal risk')

    return Response({
        'status_level': status_level,
        'status_message': status_message,
        'score': score,
        'score_label': score_label,
        'action_items': action_items,
        'sorted_items': sorted_items,
        'counts': {
            'total': len(items),
            'compliant': len(compliant),
            'overdue_legal': len(overdue_legal),
            'overdue_bp': len(overdue_bp),
            'due_soon': len(due_soon),
            'missing': len(missing),
            'open_incidents': open_incidents,
            'open_accidents': open_accidents,
        },
    })


def daysUntil_py(date_val, today):
    """Calculate days between today and a date."""
    if isinstance(date_val, str):
        from datetime import date as dt_date
        parts = date_val.split('-')
        date_val = dt_date(int(parts[0]), int(parts[1]), int(parts[2]))
    return (date_val - today).days


# ========== NATURAL LANGUAGE PARSE ==========

@api_view(['POST'])
@permission_classes([AllowAny])
def parse_command(request):
    """
    POST /api/compliance/parse-command/
    Accepts: { "text": "Upload fire risk assessment" }
    Returns: { "action": "complete", "item_id": 5, "message": "..." }
    or: { "action": "create_incident", "data": {...} }
    Uses keyword matching (Claude API integration optional future enhancement).
    """
    text = (request.data.get('text', '') or '').strip().lower()
    tenant = getattr(request, 'tenant', None)

    if not text:
        return Response({'error': 'No text provided'}, status=status.HTTP_400_BAD_REQUEST)

    items = list(ComplianceItem.objects.select_related('category').filter(category__tenant=tenant))

    # Try to match against existing compliance items
    best_match = None
    best_score = 0
    for item in items:
        title_lower = item.title.lower()
        # Exact title match
        if title_lower in text or text in title_lower:
            score = len(title_lower)
            if score > best_score:
                best_score = score
                best_match = item
        # Keyword matching
        words = title_lower.split()
        matching_words = sum(1 for w in words if w in text and len(w) > 2)
        if matching_words > best_score:
            best_score = matching_words
            best_match = item

    # Detect action type from text
    action_type = 'complete'
    if any(w in text for w in ['upload', 'uploaded', 'renew', 'renewed']):
        action_type = 'complete'
    elif any(w in text for w in ['log accident', 'accident', 'injury', 'hurt', 'cut', 'fell', 'slip']):
        action_type = 'create_accident'
    elif any(w in text for w in ['log incident', 'incident', 'near miss', 'near-miss', 'report']):
        action_type = 'create_incident'
    elif any(w in text for w in ['book', 'schedule', 'arrange']):
        action_type = 'complete'
    elif any(w in text for w in ['mark done', 'mark complete', 'completed', 'done', 'finished']):
        action_type = 'complete'

    if action_type == 'create_accident':
        return Response({
            'action': 'create_accident',
            'message': 'Ready to log an accident. Please fill in the details.',
            'parsed': {'description': text},
        })

    if action_type == 'create_incident':
        return Response({
            'action': 'create_incident',
            'message': 'Ready to report an incident. Please fill in the details.',
            'parsed': {'title': text, 'description': text},
        })

    if best_match:
        return Response({
            'action': 'complete',
            'item_id': best_match.id,
            'item_title': best_match.title,
            'item_status': best_match.status,
            'message': f'Found: "{best_match.title}". Mark as complete?',
        })

    return Response({
        'action': 'unknown',
        'message': f'Could not match "{text}" to a compliance item. Try being more specific.',
    })


# ========== INCIDENTS (IncidentReport) ==========

def _serialize_incident(inc):
    return {
        'id': inc.id,
        'title': inc.title,
        'description': inc.description,
        'severity': inc.severity,
        'status': inc.status,
        'location': inc.location,
        'incident_date': inc.incident_date.isoformat() if inc.incident_date else None,
        'reported_by': inc.reported_by.get_full_name() if inc.reported_by else '',
        'assigned_to': inc.assigned_to.get_full_name() if inc.assigned_to else '',
        'resolution_notes': inc.resolution_notes,
        'resolved_at': inc.resolved_at.isoformat() if inc.resolved_at else None,
        'riddor_reportable': getattr(inc, 'riddor_reportable', False),
        'created_at': inc.created_at.isoformat(),
    }


@api_view(['GET'])
@permission_classes([AllowAny])
def incidents_list(request):
    """GET /api/compliance/incidents/"""
    tenant = getattr(request, 'tenant', None)
    qs = IncidentReport.objects.filter(tenant=tenant)
    if request.query_params.get('status'):
        qs = qs.filter(status=request.query_params['status'])
    return Response([_serialize_incident(i) for i in qs])


@api_view(['POST'])
@permission_classes([AllowAny])
def incidents_create(request):
    """POST /api/compliance/incidents/create/"""
    d = request.data
    tenant = getattr(request, 'tenant', None)
    inc = IncidentReport.objects.create(
        tenant=tenant,
        title=d.get('title', ''),
        description=d.get('description', ''),
        severity=d.get('severity', 'MEDIUM'),
        location=d.get('location', ''),
        incident_date=d.get('incident_date') or timezone.now(),
        reported_by=request.user if request.user.is_authenticated else None,
    )
    return Response(_serialize_incident(inc), status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def incidents_status(request, incident_id):
    """POST /api/compliance/incidents/<id>/status/"""
    try:
        tenant = getattr(request, 'tenant', None)
        inc = IncidentReport.objects.get(id=incident_id, tenant=tenant)
    except IncidentReport.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    new_status = request.data.get('status', '')
    if new_status:
        inc.status = new_status
    if request.data.get('resolution_notes'):
        inc.resolution_notes = request.data['resolution_notes']
    if new_status in ('RESOLVED', 'CLOSED'):
        inc.resolved_at = timezone.now()
    inc.save()
    return Response(_serialize_incident(inc))


# ========== RAMS ==========

@api_view(['GET'])
@permission_classes([AllowAny])
def rams_list(request):
    """GET /api/compliance/rams/"""
    tenant = getattr(request, 'tenant', None)
    qs = RAMSDocument.objects.filter(tenant=tenant)
    return Response([{
        'id': r.id,
        'title': r.title,
        'reference_number': r.reference_number,
        'description': r.description,
        'document': r.document.url if r.document else None,
        'status': r.status,
        'issue_date': _safe_date(r.issue_date),
        'expiry_date': _safe_date(r.expiry_date),
        'is_expired': r.is_expired,
        'created_at': r.created_at.isoformat(),
    } for r in qs])


# ========== COMPLIANCE DOCUMENTS ==========

@api_view(['GET'])
@permission_classes([AllowAny])
def compliance_documents_list(request):
    """GET /api/compliance/documents/"""
    tenant = getattr(request, 'tenant', None)
    try:
        from documents.models import Document
        qs = Document.objects.filter(tenant=tenant)
        doc_type = request.query_params.get('type')
        if doc_type:
            qs = qs.filter(category=doc_type)
        # Filter to H&S related categories
        qs = qs.filter(category__in=['HEALTH_SAFETY', 'COMPLIANCE', 'POLICY', 'INSURANCE'])
        return Response([{
            'id': d.id,
            'title': d.title,
            'document_type': d.category,
            'is_current': not d.is_expired if hasattr(d, 'is_expired') else True,
            'is_expired': d.is_expired if hasattr(d, 'is_expired') else False,
            'expiry_date': _safe_date(d.expiry_date) if hasattr(d, 'expiry_date') else None,
        } for d in qs])
    except Exception:
        return Response([])
