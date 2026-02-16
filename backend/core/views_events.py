"""
Business Event API — Log and retrieve dashboard actions.

POST /api/events/log/         — Log a dashboard action (creates BusinessEvent)
GET  /api/events/today/       — Get today's resolved events (for Sorted view)
POST /api/events/decline/     — Decline cover and get next candidate
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models_events import BusinessEvent
from .cover_logic import get_next_candidate


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_event(request):
    """
    Log a dashboard action. Every click on the dashboard generates an event.
    No silent state mutation.

    Body:
    {
        "event_type": "COVER_REQUESTED",
        "action_label": "Ask Jordan to cover",
        "source_event_type": "staff_sick",
        "source_entity_type": "leave_request",
        "source_entity_id": 42,
        "action_detail": "Jordan is next in 7-day rotation",
        "payload": { ... }
    }
    """
    data = request.data
    event_type = data.get('event_type', '')
    action_label = data.get('action_label', '')

    if not event_type or not action_label:
        return Response(
            {'error': 'event_type and action_label are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate event_type
    valid_types = {t[0] for t in BusinessEvent.EVENT_TYPES}
    if event_type not in valid_types:
        return Response(
            {'error': f'Invalid event_type. Valid: {sorted(valid_types)}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    tenant = getattr(request, 'tenant', None)
    evt = BusinessEvent.log(
        event_type=event_type,
        action_label=action_label,
        user=request.user if request.user.is_authenticated else None,
        source_event_type=data.get('source_event_type', ''),
        source_entity_type=data.get('source_entity_type', ''),
        source_entity_id=data.get('source_entity_id'),
        action_detail=data.get('action_detail', ''),
        payload=data.get('payload', {}),
        tenant=tenant,
    )

    return Response({
        'id': evt.id,
        'event_type': evt.event_type,
        'action_label': evt.action_label,
        'status': evt.status,
        'created_at': evt.created_at.isoformat(),
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def today_resolved(request):
    """
    Return today's resolved events for the Sorted view.
    Events auto-expire from this view after 24 hours.
    All records remain in the full audit log.
    """
    tenant = getattr(request, 'tenant', None)
    events = BusinessEvent.today_resolved(tenant=tenant)

    return Response({
        'count': events.count(),
        'events': [
            {
                'id': e.id,
                'event_type': e.event_type,
                'event_type_display': e.get_event_type_display(),
                'action_label': e.action_label,
                'action_detail': e.action_detail,
                'source_event_type': e.source_event_type,
                'performed_by': e.performed_by.get_full_name() if e.performed_by else 'System',
                'created_at': e.created_at.isoformat(),
                'payload': e.payload,
            }
            for e in events
        ],
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def decline_cover(request):
    """
    Decline a cover suggestion and get the next candidate.

    Body:
    {
        "absent_staff_id": 5,
        "declined_staff_id": 12,
        "declined_staff_ids": [12, 14],   // all previously declined
        "source_entity_id": 42,
        "service_id": null
    }
    """
    data = request.data
    absent_staff_id = data.get('absent_staff_id')
    declined_staff_id = data.get('declined_staff_id')
    declined_staff_ids = data.get('declined_staff_ids', [])

    if not absent_staff_id or not declined_staff_id:
        return Response(
            {'error': 'absent_staff_id and declined_staff_id are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Log the decline event
    tenant = getattr(request, 'tenant', None)
    BusinessEvent.log(
        event_type='COVER_DECLINED',
        action_label=f'Cover declined (staff #{declined_staff_id})',
        user=request.user if request.user.is_authenticated else None,
        source_event_type='staff_sick',
        source_entity_type=data.get('source_entity_type', 'leave_request'),
        source_entity_id=data.get('source_entity_id'),
        payload={
            'absent_staff_id': absent_staff_id,
            'declined_staff_id': declined_staff_id,
        },
        tenant=tenant,
    )

    # Ensure declined_staff_id is in the list
    if declined_staff_id not in declined_staff_ids:
        declined_staff_ids.append(declined_staff_id)

    # Get service if provided
    service = None
    service_id = data.get('service_id')
    if service_id:
        try:
            from bookings.models import Service
            service = Service.objects.get(id=service_id)
        except Exception:
            pass

    next_candidate = get_next_candidate(
        absent_staff_id=absent_staff_id,
        declined_staff_ids=declined_staff_ids,
        service=service,
    )

    if next_candidate:
        return Response({
            'next_candidate': next_candidate,
            'declined_count': len(declined_staff_ids),
        })
    else:
        return Response({
            'next_candidate': None,
            'declined_count': len(declined_staff_ids),
            'message': 'No more candidates available. Consider owner cover.',
        })
