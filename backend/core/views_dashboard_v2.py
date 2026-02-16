"""
Dashboard Today V2 — Operational Incident Board API

GET /api/dashboard/today/
Returns: { state, message, events[], summary }

Feature-flagged via DASHBOARD_TODAY_V2 setting.
Falls back to 404 if flag is off.
"""
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .operational_events import get_operational_events, get_dashboard_state


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_today(request):
    """
    Operational dashboard: What happened? What do I do? Sorted.
    Returns events derived from booking, staff, and compliance deltas.
    """
    if not getattr(settings, 'DASHBOARD_TODAY_V2', True):
        return Response(
            {'error': 'Dashboard v2 not enabled for this tenant.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    lookahead = int(request.query_params.get('compliance_days', 14))
    tenant = getattr(request, 'tenant', None)
    events = get_operational_events(compliance_lookahead_days=lookahead, tenant=tenant)
    state = get_dashboard_state(events)

    # Summary counts for quick glance
    summary = {
        'total': len(events),
        'critical': sum(1 for e in events if e['severity'] == 'critical'),
        'high': sum(1 for e in events if e['severity'] == 'high'),
        'warning': sum(1 for e in events if e['severity'] == 'warning'),
        'info': sum(1 for e in events if e['severity'] == 'info'),
    }

    return Response({
        'state': state['state'],
        'message': state['message'],
        'events': events,
        'summary': summary,
    })
