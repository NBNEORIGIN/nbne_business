"""
Operational Event Aggregation Service

Derives dashboard items from deltas against expected state.
No AI. No scoring. Deterministic and procedural.

Event types:
  - staff_sick        Staff marked sick today
  - booking_cancelled Booking cancelled today
  - booking_unassigned Booking with no staff assigned
  - deposit_missing   Today's booking with no payment
  - leave_pending     Leave request pending affecting tomorrow+
  - compliance_expiry Compliance item due/overdue within threshold
  - incident_open     Open H&S incident requiring attention

Each event returns:
  {
    'event_type': str,
    'severity': 'critical' | 'high' | 'warning' | 'info',
    'summary': str,
    'detail': str,
    'actions': [{'label': str, 'reason': str, 'link': str, 'rank': int}],
    'entity_type': str,
    'entity_id': int | None,
    'timestamp': str (ISO),
  }
"""
from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.utils import timezone


def get_operational_events(compliance_lookahead_days=14, tenant=None):
    """
    Main entry point. Returns a list of operational events sorted by severity.
    Only queries modules that are enabled.
    """
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    tomorrow_end = today_start + timedelta(days=2)

    events = []

    if getattr(settings, 'BOOKINGS_MODULE_ENABLED', False):
        events.extend(_booking_events(today_start, today_end, tomorrow_end, tenant))

    if getattr(settings, 'STAFF_MODULE_ENABLED', False):
        events.extend(_staff_leave_events(today_start, today_end, tomorrow_end, tenant))

    if getattr(settings, 'COMPLIANCE_MODULE_ENABLED', False):
        events.extend(_compliance_events(today_start, compliance_lookahead_days, tenant))

    # Sort by operational priority:
    # 1) Today's operational blockers (sick staff, unassigned bookings)
    # 2) Revenue risks (deposit missing, cancelled bookings)
    # 3) Staff/rota conflicts (pending leave)
    # 4) Compliance (always last)
    category_order = {
        'staff_sick': 0,
        'booking_unassigned': 1,
        'incident_open': 2,
        'deposit_missing': 3,
        'booking_cancelled': 4,
        'leave_pending': 5,
        'compliance_expiry': 6,
    }
    events.sort(key=lambda e: category_order.get(e['event_type'], 99))

    return events


def get_dashboard_state(events):
    """
    Returns the overall dashboard state.
    'sorted' if no unresolved events, otherwise 'active'.
    """
    if not events:
        return {
            'state': 'sorted',
            'message': 'No active issues. Sorted.',
        }

    total = len(events)
    return {
        'state': 'active',
        'message': f'{total} issue{"s" if total != 1 else ""} need{"" if total != 1 else "s"} attention.',
    }


# ---------------------------------------------------------------------------
# Booking events
# ---------------------------------------------------------------------------

def _booking_events(today_start, today_end, tomorrow_end, tenant=None):
    from bookings.models import Booking, Staff as BookingStaff

    events = []
    t_filter = {'tenant': tenant} if tenant else {}

    # 1. Bookings cancelled today
    cancelled_today = Booking.objects.filter(
        **t_filter,
        updated_at__gte=today_start,
        updated_at__lt=today_end,
        status='cancelled',
    ).select_related('client', 'service', 'staff')

    for b in cancelled_today:
        client_name = b.client.name if b.client else 'Unknown client'
        price = b.service.price or Decimal('0')
        events.append({
            'event_type': 'booking_cancelled',
            'severity': 'warning',
            'summary': f'Booking cancelled: {client_name}',
            'detail': f'{client_name} cancelled {b.service.name} at {b.start_time.strftime("%H:%M")}.',
            'why_it_matters': f'Slot now open. £{price:.2f} revenue gap.' if price > 0 else 'Slot now open for rebooking.',
            'actions': [
                {'label': 'Review slot', 'reason': 'Slot now available for rebooking', 'link': '/admin/bookings', 'rank': 1},
            ],
            'entity_type': 'booking',
            'entity_id': b.id,
            'timestamp': b.updated_at.isoformat(),
        })

    # 2. Bookings with no staff assigned (today or tomorrow)
    unassigned = Booking.objects.filter(
        **t_filter,
        start_time__gte=today_start,
        start_time__lt=tomorrow_end,
        staff__isnull=True,
        status__in=['confirmed', 'pending'],
    ).select_related('client', 'service')

    for b in unassigned:
        client_name = b.client.name if b.client else 'Unknown client'
        is_today = b.start_time < today_end
        sev = 'critical' if is_today else 'high'
        when = 'today' if is_today else 'tomorrow'

        # Deterministic action: suggest available staff for this service
        available_staff = list(
            BookingStaff.objects.filter(
                services=b.service, active=True
            ).values_list('name', flat=True)[:3]
        )
        actions = []
        for i, name in enumerate(available_staff):
            actions.append({
                'label': f'Assign {name}',
                'reason': f'Available for {b.service.name}',
                'link': '/admin/bookings',
                'rank': i + 1,
            })
        if not actions:
            actions.append({
                'label': 'No staff available — reschedule or cancel',
                'reason': 'No active staff linked to this service',
                'link': '/admin/bookings',
                'rank': 1,
            })

        events.append({
            'event_type': 'booking_unassigned',
            'severity': sev,
            'summary': f'Unassigned booking {when}: {client_name}',
            'detail': f'{b.start_time.strftime("%H:%M")} {b.service.name} for {client_name} has no stylist.',
            'why_it_matters': f'No one assigned — booking at risk ({when}).',
            'actions': actions,
            'entity_type': 'booking',
            'entity_id': b.id,
            'timestamp': b.created_at.isoformat(),
        })

    # 3. Today's bookings with no payment (deposit missing)
    unpaid_today = Booking.objects.filter(
        **t_filter,
        start_time__gte=today_start,
        start_time__lt=today_end,
        status__in=['confirmed', 'pending'],
        payment_status='pending',
    ).select_related('client', 'service').exclude(
        service__price=Decimal('0')
    )

    for b in unpaid_today:
        client_name = b.client.name if b.client else 'Unknown client'
        price = b.service.price or Decimal('0')
        events.append({
            'event_type': 'deposit_missing',
            'severity': 'high',
            'summary': f'No payment: {client_name} (£{price:.2f})',
            'detail': f'{client_name}\u2019s {b.service.name} at {b.start_time.strftime("%H:%M")} has no deposit.',
            'why_it_matters': f'£{price:.2f} revenue at risk.',
            'actions': [
                {'label': 'Request payment', 'reason': f'£{price:.2f} outstanding', 'link': '/admin/bookings', 'rank': 1},
                {'label': 'Mark as paid', 'reason': 'If payment received offline', 'link': '/admin/bookings', 'rank': 2},
                {'label': 'Cancel booking', 'reason': 'If client unresponsive', 'link': '/admin/bookings', 'rank': 3},
            ],
            'entity_type': 'booking',
            'entity_id': b.id,
            'timestamp': b.created_at.isoformat(),
        })

    return events


# ---------------------------------------------------------------------------
# Staff / Leave events
# ---------------------------------------------------------------------------

def _staff_leave_events(today_start, today_end, tomorrow_end, tenant=None):
    events = []

    try:
        from bookings.models_availability import LeaveRequest
    except ImportError:
        return events

    # 1. Staff on sick leave today
    sick_today = LeaveRequest.objects.filter(
        leave_type='SICK',
        start_datetime__lt=today_end,
        end_datetime__gt=today_start,
        status__in=['APPROVED', 'REQUESTED'],
    ).select_related('staff_member')

    for lv in sick_today:
        staff_name = lv.staff_member.name

        # Count affected bookings
        from bookings.models import Booking
        affected_count = Booking.objects.filter(
            staff=lv.staff_member,
            start_time__gte=today_start,
            start_time__lt=today_end,
            status__in=['confirmed', 'pending'],
        ).count()

        # Deterministic cover suggestion via cover_logic
        from core.cover_logic import get_cover_candidates
        candidates = get_cover_candidates(
            absent_staff_id=lv.staff_member_id,
            strategy='rotation',
            max_candidates=3,
        )

        actions = []
        for c in candidates:
            actions.append({
                'label': f'Ask {c["name"]} to cover',
                'reason': c['reason'],
                'link': '/admin/staff',
                'rank': c['rank'],
                'staff_id': c['staff_id'],
            })
        actions.append({
            'label': 'Owner cover',
            'reason': 'If no staff available',
            'link': '/admin/staff',
            'rank': len(actions) + 1,
        })

        affected_text = f'{affected_count} booking{"s" if affected_count != 1 else ""} affected' if affected_count else 'No bookings affected'

        events.append({
            'event_type': 'staff_sick',
            'severity': 'critical',
            'summary': f'{staff_name} off sick today',
            'detail': f'{staff_name} is off today. {affected_text}.',
            'why_it_matters': f'{affected_text}' if affected_count else 'Rota gap — may need cover',
            'actions': actions,
            'entity_type': 'leave_request',
            'entity_id': lv.id,
            'timestamp': lv.created_at.isoformat(),
        })

    # 2. Pending leave requests affecting tomorrow onwards
    pending_leave = LeaveRequest.objects.filter(
        status='REQUESTED',
        start_datetime__lt=today_start + timedelta(days=7),
        end_datetime__gt=today_start,
    ).select_related('staff_member')

    for lv in pending_leave:
        # Skip sick leave already handled above
        if lv.leave_type == 'SICK' and lv.start_datetime < today_end:
            continue

        staff_name = lv.staff_member.name
        start_str = lv.start_datetime.strftime('%d %b')
        end_str = lv.end_datetime.strftime('%d %b')

        events.append({
            'event_type': 'leave_pending',
            'severity': 'warning',
            'summary': f'Leave request pending: {staff_name}',
            'detail': f'{staff_name} requested {lv.get_leave_type_display().lower()} {start_str} to {end_str}.',
            'why_it_matters': 'Needs approval — may require cover arrangement.',
            'actions': [
                {'label': 'Approve', 'reason': 'If cover arranged', 'link': '/admin/staff', 'rank': 1},
                {'label': 'Decline', 'reason': 'If no cover available', 'link': '/admin/staff', 'rank': 2},
            ],
            'entity_type': 'leave_request',
            'entity_id': lv.id,
            'timestamp': lv.created_at.isoformat(),
        })

    return events


# ---------------------------------------------------------------------------
# Compliance events
# ---------------------------------------------------------------------------

def _compliance_events(today_start, lookahead_days, tenant=None):
    events = []

    try:
        from compliance.models import ComplianceItem, IncidentReport
    except ImportError:
        return events

    today = today_start.date()
    t_filter = {'category__tenant': tenant} if tenant else {}
    t_filter_direct = {'tenant': tenant} if tenant else {}

    # 1. Overdue compliance items
    overdue = ComplianceItem.objects.filter(
        **t_filter,
        status='OVERDUE',
    ).select_related('category')

    for item in overdue:
        req_type = 'Legal requirement' if item.item_type == 'LEGAL' else 'Best practice'
        events.append({
            'event_type': 'compliance_expiry',
            'severity': 'critical' if item.item_type == 'LEGAL' else 'high',
            'summary': f'Overdue: {item.title}',
            'detail': f'{item.title} ({item.category.name}) is overdue.',
            'why_it_matters': f'{req_type} — overdue since {item.next_due_date or item.due_date or "unknown"}.',
            'actions': [
                {'label': 'Complete now', 'reason': f'{req_type} — overdue', 'link': '/admin/compliance', 'rank': 1},
            ],
            'entity_type': 'compliance_item',
            'entity_id': item.id,
            'timestamp': item.updated_at.isoformat(),
        })

    # 2. Due soon (within lookahead)
    due_soon_date = today + timedelta(days=lookahead_days)
    due_soon = ComplianceItem.objects.filter(
        **t_filter,
        status='DUE_SOON',
        next_due_date__lte=due_soon_date,
    ).select_related('category')

    for item in due_soon:
        days_until = (item.next_due_date - today).days if item.next_due_date else 0
        events.append({
            'event_type': 'compliance_expiry',
            'severity': 'warning' if days_until > 7 else 'high',
            'summary': f'Due in {days_until} day{"s" if days_until != 1 else ""}: {item.title}',
            'detail': f'{item.title} ({item.category.name}) due in {days_until} day{"s" if days_until != 1 else ""}.',
            'why_it_matters': f'{days_until} day{"s" if days_until != 1 else ""} remaining.',
            'actions': [
                {'label': 'Schedule completion', 'reason': f'{days_until} days remaining', 'link': '/admin/compliance', 'rank': 1},
            ],
            'entity_type': 'compliance_item',
            'entity_id': item.id,
            'timestamp': item.updated_at.isoformat(),
        })

    # 3. Open incidents
    open_incidents = IncidentReport.objects.filter(
        **t_filter_direct,
        status__in=['OPEN', 'INVESTIGATING'],
    )

    for inc in open_incidents:
        events.append({
            'event_type': 'incident_open',
            'severity': 'critical' if inc.severity == 'HIGH' else 'warning',
            'summary': f'Open incident: {inc.title}',
            'detail': f'{inc.title} at {inc.location}. Reported {inc.incident_date.strftime("%d %b")}.',
            'why_it_matters': f'{inc.get_severity_display()} severity — requires attention.',
            'actions': [
                {'label': 'Investigate', 'reason': f'{inc.get_severity_display()} severity', 'link': '/admin/compliance', 'rank': 1},
                {'label': 'Resolve', 'reason': 'If investigation complete', 'link': '/admin/compliance', 'rank': 2},
            ],
            'entity_type': 'incident',
            'entity_id': inc.id,
            'timestamp': inc.created_at.isoformat(),
        })

    return events
