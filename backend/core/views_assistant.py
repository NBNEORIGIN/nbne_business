"""
Assistant Parse Endpoint — Stateless command parser.

POST /api/assistant/parse/

Takes natural language text from the global command bar and returns
a structured JSON command object. Never modifies the database directly.
Owner must confirm before execution.

Rules:
- Stateless parser — no memory between calls
- Returns structured intent only
- Owner confirms
- Backend validates
- Event created
- Deterministic engine executes
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


# Keyword-to-event-type mapping for deterministic parsing
PARSE_RULES = [
    # Staff / cover
    {
        'keywords': ['sick', 'off sick', 'called in sick', 'unwell', 'ill'],
        'event_type': 'STAFF_SICK',
        'action': 'log_sick',
        'description': 'Mark staff member as sick',
    },
    {
        'keywords': ['cover', 'ask to cover', 'request cover', 'fill in'],
        'event_type': 'COVER_REQUESTED',
        'action': 'request_cover',
        'description': 'Request cover from another staff member',
    },
    # Bookings
    {
        'keywords': ['assign', 'assign to', 'give to'],
        'event_type': 'BOOKING_ASSIGNED',
        'action': 'assign_booking',
        'description': 'Assign a booking to a staff member',
    },
    {
        'keywords': ['cancel booking', 'cancel appointment'],
        'event_type': 'BOOKING_CANCELLED',
        'action': 'cancel_booking',
        'description': 'Cancel a booking',
    },
    {
        'keywords': ['reschedule', 'move booking', 'move appointment'],
        'event_type': 'BOOKING_RESCHEDULED',
        'action': 'reschedule_booking',
        'description': 'Reschedule a booking',
    },
    # Payments
    {
        'keywords': ['request payment', 'chase payment', 'send payment request', 'deposit'],
        'event_type': 'PAYMENT_REQUESTED',
        'action': 'request_payment',
        'description': 'Send a payment request to a client',
    },
    {
        'keywords': ['mark as paid', 'mark paid', 'payment received'],
        'event_type': 'PAYMENT_MARKED',
        'action': 'mark_paid',
        'description': 'Mark a booking as paid',
    },
    # Leave
    {
        'keywords': ['approve leave', 'approve holiday', 'approve time off'],
        'event_type': 'LEAVE_APPROVED',
        'action': 'approve_leave',
        'description': 'Approve a leave request',
    },
    {
        'keywords': ['decline leave', 'reject leave', 'deny leave'],
        'event_type': 'LEAVE_DECLINED',
        'action': 'decline_leave',
        'description': 'Decline a leave request',
    },
    # Compliance
    {
        'keywords': ['complete compliance', 'mark compliant', 'compliance done'],
        'event_type': 'COMPLIANCE_COMPLETED',
        'action': 'complete_compliance',
        'description': 'Mark a compliance item as completed',
    },
    {
        'keywords': ['resolve incident', 'close incident'],
        'event_type': 'INCIDENT_RESOLVED',
        'action': 'resolve_incident',
        'description': 'Resolve an open incident',
    },
    # Staff module — shifts / timesheets / hours / training
    {
        'keywords': ['add shift', 'create shift', 'new shift', 'schedule shift'],
        'event_type': 'SHIFT_CREATED',
        'action': 'add_shift',
        'description': 'Add a new shift to the rota',
    },
    {
        'keywords': ['generate timesheets', 'create timesheets', 'build timesheets'],
        'event_type': 'TIMESHEETS_GENERATED',
        'action': 'generate_timesheets',
        'description': 'Generate timesheet entries from working hours',
    },
    {
        'keywords': ['export timesheets', 'download timesheets', 'payroll csv', 'export csv', 'download csv', 'export payroll'],
        'event_type': 'TIMESHEETS_EXPORTED',
        'action': 'export_timesheets',
        'description': 'Export timesheets as CSV for payroll',
    },
    {
        'keywords': ['add staff', 'new staff', 'hire staff', 'create staff', 'new employee', 'add team member'],
        'event_type': 'STAFF_ADDED',
        'action': 'add_staff',
        'description': 'Add a new staff member',
    },
    {
        'keywords': ['training expired', 'expired training', 'overdue training', 'training due', 'check training'],
        'event_type': 'TRAINING_CHECK',
        'action': 'check_training',
        'description': 'Check for expired or due training records',
    },
    {
        'keywords': ['set hours', 'set working hours', 'update hours', 'change hours'],
        'event_type': 'HOURS_UPDATED',
        'action': 'set_hours',
        'description': 'Update working hours for a staff member',
    },
    {
        'keywords': ['running late', 'late today', 'late arrival', 'will be late'],
        'event_type': 'STAFF_LATE',
        'action': 'log_late',
        'description': 'Log a late arrival for a staff member',
    },
]

# Common staff name patterns to extract
ENTITY_EXTRACTORS = {
    'staff_name': None,  # Extracted dynamically from DB
}


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def parse_command(request):
    """
    Parse natural language input into a structured command.

    Body: { "text": "Chloe is off sick today" }

    Returns:
    {
        "parsed": true,
        "intent": {
            "event_type": "STAFF_SICK",
            "action": "log_sick",
            "description": "Mark staff member as sick",
            "entities": { "staff_name": "Chloe" },
            "confidence": "keyword_match",
            "original_text": "Chloe is off sick today"
        },
        "confirmation_required": true,
        "confirmation_message": "Mark Chloe as sick today?"
    }
    """
    text = request.data.get('text', '').strip()

    if not text:
        return Response(
            {'error': 'text is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    text_lower = text.lower()

    # 1. Match intent by keywords
    matched_rule = None
    matched_keyword = None
    for rule in PARSE_RULES:
        for kw in rule['keywords']:
            if kw in text_lower:
                matched_rule = rule
                matched_keyword = kw
                break
        if matched_rule:
            break

    if not matched_rule:
        return Response({
            'parsed': False,
            'intent': None,
            'message': 'Could not understand that command. Try something like: "Chloe is off sick" or "Assign Sam to the 11:00 booking".',
        })

    # 2. Extract entities (staff names from DB)
    entities = _extract_entities(text)

    # 3. Build confirmation message
    confirmation = _build_confirmation(matched_rule, entities, text)

    return Response({
        'parsed': True,
        'intent': {
            'event_type': matched_rule['event_type'],
            'action': matched_rule['action'],
            'description': matched_rule['description'],
            'entities': entities,
            'confidence': 'keyword_match',
            'matched_keyword': matched_keyword,
            'original_text': text,
        },
        'confirmation_required': True,
        'confirmation_message': confirmation,
    })


def _extract_entities(text):
    """Extract known entity names from the text using DB lookup."""
    entities = {}

    try:
        from bookings.models import Staff as BookingStaff, Client
        staff_names = list(BookingStaff.objects.filter(active=True).values_list('name', flat=True))
        for name in staff_names:
            if name.lower() in text.lower() or name.split()[0].lower() in text.lower():
                entities['staff_name'] = name
                break

        client_names = list(Client.objects.values_list('name', flat=True)[:100])
        for name in client_names:
            if name.lower() in text.lower():
                entities['client_name'] = name
                break
    except Exception:
        pass

    # Also check StaffProfile names (staff module)
    if 'staff_name' not in entities:
        try:
            from staff.models import StaffProfile
            profiles = StaffProfile.objects.filter(is_active=True).select_related('user')
            for p in profiles:
                display = f"{p.user.first_name} {p.user.last_name}".strip()
                first = p.user.first_name.strip()
                if display and display.lower() in text.lower():
                    entities['staff_name'] = display
                    entities['staff_id'] = p.id
                    break
                elif first and first.lower() in text.lower():
                    entities['staff_name'] = display or first
                    entities['staff_id'] = p.id
                    break
        except Exception:
            pass

    return entities


def _build_confirmation(rule, entities, original_text):
    """Build a human-readable confirmation message."""
    staff = entities.get('staff_name', '')
    client = entities.get('client_name', '')

    templates = {
        'STAFF_SICK': f'Mark {staff} as sick today?' if staff else 'Mark staff member as sick today?',
        'COVER_REQUESTED': f'Request cover from {staff}?' if staff else 'Request cover?',
        'BOOKING_ASSIGNED': f'Assign {staff} to this booking?' if staff else 'Assign staff to booking?',
        'BOOKING_CANCELLED': f'Cancel booking for {client}?' if client else 'Cancel this booking?',
        'BOOKING_RESCHEDULED': f'Reschedule booking for {client}?' if client else 'Reschedule this booking?',
        'PAYMENT_REQUESTED': f'Send payment request to {client}?' if client else 'Send payment request?',
        'PAYMENT_MARKED': f'Mark payment as received for {client}?' if client else 'Mark as paid?',
        'LEAVE_APPROVED': f'Approve leave for {staff}?' if staff else 'Approve this leave request?',
        'LEAVE_DECLINED': f'Decline leave for {staff}?' if staff else 'Decline this leave request?',
        'COMPLIANCE_COMPLETED': 'Mark compliance item as completed?',
        'INCIDENT_RESOLVED': 'Resolve this incident?',
        'SHIFT_CREATED': f'Add a shift for {staff}?' if staff else 'Add a new shift?',
        'TIMESHEETS_GENERATED': 'Generate timesheets from working hours for this period?',
        'TIMESHEETS_EXPORTED': 'Download payroll CSV for the current period?',
        'STAFF_ADDED': 'Add a new staff member?',
        'TRAINING_CHECK': f'Check training status for {staff}?' if staff else 'Check for expired or due training?',
        'HOURS_UPDATED': f'Update working hours for {staff}?' if staff else 'Update working hours?',
        'STAFF_LATE': f'Log {staff} as arriving late today?' if staff else 'Log a late arrival?',
    }

    return templates.get(rule['event_type'], f'Execute: {rule["description"]}?')
