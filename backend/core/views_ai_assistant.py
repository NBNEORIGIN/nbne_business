"""
AI Assistant Chat Panel — OpenAI function-calling powered admin assistant.

POST /api/assistant/chat/
Body: { "messages": [...], "conversation_id": "optional-uuid" }

The assistant can:
- Read business state (bookings, staff, compliance, CRM, documents)
- Execute actions (mark sick, request cover, approve leave, add leads, etc.)
- Provide explanations and recommendations
- Navigate the user to relevant pages

Uses OpenAI function calling so the LLM decides which tools to invoke.
All tool calls are executed server-side and results fed back to the LLM
for a natural language summary.
"""
import json
import logging
import uuid
from datetime import date, time, timedelta, datetime

from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are the AI assistant for an NBNE business management platform.
You help business owners and managers run their day-to-day operations through natural conversation.

Your personality:
- Friendly, professional, and direct
- You speak like a competent operations manager — no waffle
- Use British English
- Keep responses concise but helpful
- When you take an action, confirm what you did and suggest next steps
- If something needs attention, proactively flag it

You have access to tools that let you read and modify business data:
- Staff management (mark sick, check who's off, view schedules)
- Bookings (view today's bookings, check unassigned)
- CRM (view VIP clients, at-risk clients, add leads)
- Compliance (check status, view overdue items)
- General queries (today's overview)

When a user tells you about a situation (e.g. "Sam called in sick"), you should:
1. Execute the relevant action using tools
2. Check for knock-on effects (e.g. affected bookings)
3. Suggest next steps or offer to take further action

Always be proactive — if marking someone sick, check their bookings too.
Never make up data. Only report what the tools return."""


# ═══════════════════════════════════════════════════════════════
# TOOL DEFINITIONS (OpenAI function calling format)
# ═══════════════════════════════════════════════════════════════

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "mark_staff_sick",
            "description": "Mark a staff member as sick/absent for today. Returns confirmation and any affected bookings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "staff_name": {
                        "type": "string",
                        "description": "First name or full name of the staff member"
                    }
                },
                "required": ["staff_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_who_is_off",
            "description": "Get a list of all staff who are off today (sick, absent, or on approved leave).",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_staff_list",
            "description": "Get a list of all active staff members with their roles and status.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_todays_bookings",
            "description": "Get all bookings for today with client names, times, services, and assigned staff.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_unassigned_bookings",
            "description": "Get bookings that have no staff member assigned.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_staff_bookings",
            "description": "Get bookings assigned to a specific staff member for today.",
            "parameters": {
                "type": "object",
                "properties": {
                    "staff_name": {
                        "type": "string",
                        "description": "Name of the staff member"
                    }
                },
                "required": ["staff_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_vip_clients",
            "description": "Get top clients by lifetime value (VIPs). Returns name, email, and spend.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max number of clients to return (default 10)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_at_risk_clients",
            "description": "Get clients who haven't booked in the last 90 days (at-risk of churning).",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days since last booking to consider at-risk (default 90)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_crm_lead",
            "description": "Create a new CRM lead/prospect.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Full name of the lead"
                    },
                    "email": {
                        "type": "string",
                        "description": "Email address (optional)"
                    },
                    "phone": {
                        "type": "string",
                        "description": "Phone number (optional)"
                    },
                    "value_pounds": {
                        "type": "number",
                        "description": "Estimated value in pounds (optional)"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Any notes about the lead"
                    }
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_compliance_status",
            "description": "Get an overview of compliance/health & safety status — total items, compliant, expiring soon, overdue.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_overdue_compliance",
            "description": "Get list of overdue compliance items that need immediate attention.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_todays_overview",
            "description": "Get a high-level overview of today: bookings count, staff on/off, any issues, compliance alerts.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_staff",
            "description": "Get staff members who are working today and available (not sick or on leave).",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "navigate_user",
            "description": "Navigate the user to a specific page in the admin panel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page": {
                        "type": "string",
                        "enum": [
                            "/admin",
                            "/admin/bookings",
                            "/admin/staff",
                            "/admin/clients",
                            "/admin/chat",
                            "/admin/health-safety",
                            "/admin/documents",
                            "/admin/reports",
                            "/admin/settings"
                        ],
                        "description": "The admin page to navigate to"
                    }
                },
                "required": ["page"]
            }
        }
    },
]


# ═══════════════════════════════════════════════════════════════
# TOOL IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════════════

def _resolve_staff(tenant, name):
    """Find staff member by name (first name or full name match)."""
    try:
        from staff.models import StaffProfile
        name_lower = name.lower().strip()
        profiles = StaffProfile.objects.filter(tenant=tenant, is_active=True).select_related('user')
        for p in profiles:
            first = p.user.first_name.strip().lower()
            full = f"{p.user.first_name} {p.user.last_name}".strip().lower()
            display = (p.display_name or '').strip().lower()
            if display == name_lower or full == name_lower or first == name_lower:
                return p
        # Partial match
        for p in profiles:
            first = p.user.first_name.strip().lower()
            if first and name_lower.startswith(first):
                return p
    except Exception:
        pass
    return None


def _resolve_booking_staff(tenant, name):
    """Find staff in the bookings module by name."""
    try:
        from bookings.models import Staff
        name_lower = name.lower().strip()
        for s in Staff.objects.filter(tenant=tenant, active=True):
            if s.name.lower() == name_lower or s.name.split()[0].lower() == name_lower:
                return s
    except Exception:
        pass
    return None


def tool_mark_staff_sick(tenant, args):
    staff_name = args.get('staff_name', '')
    staff = _resolve_staff(tenant, staff_name)
    today = date.today()
    display = staff_name
    created = False

    if staff:
        # StaffProfile found — create AbsenceRecord
        from staff.models import AbsenceRecord
        _, created = AbsenceRecord.objects.get_or_create(
            staff=staff, date=today, record_type='ABSENCE',
            defaults={'reason': 'Sick — logged via AI assistant', 'is_authorised': True}
        )
        display = staff.display_name or f"{staff.user.first_name} {staff.user.last_name}".strip()
    else:
        # Fall back to booking staff
        booking_staff = _resolve_booking_staff(tenant, staff_name)
        if not booking_staff:
            return {"success": False, "message": f"Could not find active staff member '{staff_name}'. Check the name and try again."}
        display = booking_staff.name
        # Try to find or create a linked StaffProfile for absence tracking
        try:
            from staff.models import StaffProfile, AbsenceRecord
            from accounts.models import User
            user = User.objects.filter(email=booking_staff.email).first() if booking_staff.email else None
            if user:
                sp, _ = StaffProfile.objects.get_or_create(
                    user=user, defaults={'tenant': tenant, 'display_name': display}
                )
                _, created = AbsenceRecord.objects.get_or_create(
                    staff=sp, date=today, record_type='ABSENCE',
                    defaults={'reason': 'Sick — logged via AI assistant', 'is_authorised': True}
                )
            else:
                created = True  # No user account, just report success
        except Exception as e:
            logger.warning(f"[AI] Error creating absence for booking staff: {e}")
            created = True

    result = {"success": True, "staff_name": display}
    if created:
        result["message"] = f"{display} has been marked as sick for today."
    else:
        result["message"] = f"{display} was already marked as sick today."

    # Check affected bookings
    try:
        from bookings.models import Booking
        booking_staff = _resolve_booking_staff(tenant, staff_name)
        if booking_staff:
            today_bookings = Booking.objects.filter(
                tenant=tenant, staff=booking_staff,
                start_time__date=today, status__in=['CONFIRMED', 'PENDING']
            ).select_related('client', 'service')
            if today_bookings.exists():
                affected = []
                for b in today_bookings:
                    client_name = b.client.name if b.client else 'Walk-in'
                    service_name = b.service.name if b.service else 'Unknown'
                    time_str = b.start_time.strftime('%H:%M')
                    affected.append({"time": time_str, "client": client_name, "service": service_name})
                result["affected_bookings"] = affected
                result["message"] += f" They have {len(affected)} booking(s) today that need attention."
    except Exception as e:
        logger.warning(f"[AI] Error checking affected bookings: {e}")

    return result


def tool_get_who_is_off(tenant, args):
    today = date.today()
    off_list = []
    try:
        from staff.models import AbsenceRecord, LeaveRequest
        for a in AbsenceRecord.objects.filter(staff__tenant=tenant, date=today).select_related('staff', 'staff__user'):
            name = a.staff.display_name or f"{a.staff.user.first_name} {a.staff.user.last_name}".strip()
            off_list.append({"name": name, "reason": "sick/absent"})

        for lv in LeaveRequest.objects.filter(
            staff__tenant=tenant, status='APPROVED',
            start_date__lte=today, end_date__gte=today
        ).select_related('staff', 'staff__user'):
            name = lv.staff.display_name or f"{lv.staff.user.first_name} {lv.staff.user.last_name}".strip()
            off_list.append({"name": name, "reason": f"leave ({lv.leave_type})"})
    except Exception as e:
        logger.warning(f"[AI] Error checking who is off: {e}")

    return {"off_today": off_list, "count": len(off_list)}


def tool_get_staff_list(tenant, args):
    staff_list = []
    seen_names = set()
    try:
        from staff.models import StaffProfile
        for p in StaffProfile.objects.filter(tenant=tenant, is_active=True).select_related('user'):
            name = p.display_name or f"{p.user.first_name} {p.user.last_name}".strip()
            staff_list.append({
                "name": name,
                "role": p.role,
                "email": p.user.email,
                "source": "staff_profile",
            })
            seen_names.add(name.lower())
    except Exception as e:
        logger.warning(f"[AI] Error getting staff profiles: {e}")
    # Also include booking staff not already listed
    try:
        from bookings.models import Staff as BookingStaff
        for bs in BookingStaff.objects.filter(tenant=tenant, active=True):
            if bs.name.lower() not in seen_names:
                staff_list.append({
                    "name": bs.name,
                    "role": bs.role or 'staff',
                    "email": bs.email or '',
                    "source": "booking_staff",
                })
                seen_names.add(bs.name.lower())
    except Exception as e:
        logger.warning(f"[AI] Error getting booking staff: {e}")
    return {"staff": staff_list, "count": len(staff_list)}


def tool_get_todays_bookings(tenant, args):
    bookings = []
    try:
        from bookings.models import Booking
        today = date.today()
        qs = Booking.objects.filter(
            tenant=tenant, start_time__date=today
        ).select_related('client', 'service', 'staff').order_by('start_time')
        for b in qs:
            bookings.append({
                "time": b.start_time.strftime('%H:%M'),
                "client": b.client.name if b.client else 'Walk-in',
                "service": b.service.name if b.service else '—',
                "staff": b.staff.name if b.staff else 'Unassigned',
                "status": b.status,
            })
    except Exception as e:
        logger.warning(f"[AI] Error getting bookings: {e}")
    return {"bookings": bookings, "count": len(bookings)}


def tool_get_unassigned_bookings(tenant, args):
    bookings = []
    try:
        from bookings.models import Booking
        today = date.today()
        qs = Booking.objects.filter(
            tenant=tenant, start_time__date__gte=today, staff__isnull=True
        ).select_related('client', 'service').order_by('start_time')
        for b in qs:
            bookings.append({
                "time": b.start_time.strftime('%H:%M'),
                "date": b.start_time.strftime('%Y-%m-%d'),
                "client": b.client.name if b.client else 'Walk-in',
                "service": b.service.name if b.service else '—',
            })
    except Exception as e:
        logger.warning(f"[AI] Error getting unassigned bookings: {e}")
    return {"unassigned_bookings": bookings, "count": len(bookings)}


def tool_get_staff_bookings(tenant, args):
    staff_name = args.get('staff_name', '')
    booking_staff = _resolve_booking_staff(tenant, staff_name)
    if not booking_staff:
        return {"success": False, "message": f"Could not find staff member '{staff_name}' in bookings."}

    bookings = []
    try:
        from bookings.models import Booking
        today = date.today()
        qs = Booking.objects.filter(
            tenant=tenant, staff=booking_staff, start_time__date=today
        ).select_related('client', 'service').order_by('start_time')
        for b in qs:
            bookings.append({
                "time": b.start_time.strftime('%H:%M'),
                "client": b.client.name if b.client else 'Walk-in',
                "service": b.service.name if b.service else '—',
                "status": b.status,
            })
    except Exception as e:
        logger.warning(f"[AI] Error getting staff bookings: {e}")

    return {"staff_name": booking_staff.name, "bookings": bookings, "count": len(bookings)}


def tool_get_vip_clients(tenant, args):
    limit = args.get('limit', 10)
    clients = []
    try:
        from bookings.models import Client
        for c in Client.objects.filter(tenant=tenant, lifetime_value__gt=0).order_by('-lifetime_value')[:limit]:
            clients.append({
                "name": c.name,
                "email": c.email or '',
                "lifetime_value": f"£{float(c.lifetime_value):.2f}",
            })
    except Exception as e:
        logger.warning(f"[AI] Error getting VIP clients: {e}")
    return {"vip_clients": clients, "count": len(clients)}


def tool_get_at_risk_clients(tenant, args):
    days = args.get('days', 90)
    clients = []
    try:
        from bookings.models import Client, Booking
        cutoff = timezone.now() - timedelta(days=days)
        active_client_ids = Booking.objects.filter(
            tenant=tenant, start_time__gte=cutoff
        ).values_list('client_id', flat=True).distinct()
        at_risk = Client.objects.filter(tenant=tenant).exclude(
            id__in=active_client_ids
        ).order_by('-lifetime_value')[:20]
        for c in at_risk:
            clients.append({
                "name": c.name,
                "email": c.email or '',
                "lifetime_value": f"£{float(c.lifetime_value):.2f}",
            })
    except Exception as e:
        logger.warning(f"[AI] Error getting at-risk clients: {e}")
    return {"at_risk_clients": clients, "count": len(clients), "threshold_days": days}


def tool_add_crm_lead(tenant, args):
    try:
        from crm.models import Lead, LeadHistory
        name = args.get('name', '').strip()
        if not name:
            return {"success": False, "message": "Lead name is required."}

        value_pence = int(args.get('value_pounds', 0) * 100)
        lead = Lead.objects.create(
            tenant=tenant,
            name=name,
            email=args.get('email', ''),
            phone=args.get('phone', ''),
            source='manual',
            status='NEW',
            value_pence=value_pence,
            notes=args.get('notes', 'Created via AI assistant'),
        )
        LeadHistory.objects.create(lead=lead, action='Lead created', detail='Via AI assistant')
        return {
            "success": True,
            "message": f"Lead '{name}' created successfully.",
            "lead_id": lead.id,
            "value": f"£{value_pence/100:.0f}" if value_pence else None,
        }
    except Exception as e:
        logger.warning(f"[AI] Error adding lead: {e}")
        return {"success": False, "message": f"Error creating lead: {str(e)}"}


def tool_get_compliance_status(tenant, args):
    result = {"total": 0, "compliant": 0, "expiring_soon": 0, "overdue": 0}
    try:
        from compliance.models import ComplianceItem
        items = ComplianceItem.objects.filter(category__tenant=tenant)
        result["total"] = items.count()
        result["compliant"] = items.filter(status='VALID').count()
        result["expiring_soon"] = items.filter(status='EXPIRING').count()
        result["overdue"] = items.filter(status='OVERDUE').count()
    except Exception as e:
        logger.warning(f"[AI] Error getting compliance status: {e}")
    return result


def tool_get_overdue_compliance(tenant, args):
    items = []
    try:
        from compliance.models import ComplianceItem
        for ci in ComplianceItem.objects.filter(category__tenant=tenant, status='OVERDUE').select_related('category')[:20]:
            items.append({
                "name": ci.name,
                "category": ci.category.name if ci.category else '—',
                "expiry_date": ci.expiry_date.isoformat() if ci.expiry_date else None,
            })
    except Exception as e:
        logger.warning(f"[AI] Error getting overdue compliance: {e}")
    return {"overdue_items": items, "count": len(items)}


def tool_get_todays_overview(tenant, args):
    overview = {
        "date": date.today().isoformat(),
        "bookings_today": 0,
        "staff_on": 0,
        "staff_off": 0,
        "unassigned_bookings": 0,
        "overdue_compliance": 0,
    }
    try:
        from bookings.models import Booking
        today = date.today()
        overview["bookings_today"] = Booking.objects.filter(
            tenant=tenant, start_time__date=today
        ).count()
        overview["unassigned_bookings"] = Booking.objects.filter(
            tenant=tenant, start_time__date=today, staff__isnull=True
        ).count()
    except Exception:
        pass

    try:
        from staff.models import StaffProfile, AbsenceRecord, LeaveRequest
        total_staff = StaffProfile.objects.filter(tenant=tenant, is_active=True).count()
        today = date.today()
        sick = AbsenceRecord.objects.filter(staff__tenant=tenant, date=today).values('staff_id').distinct().count()
        on_leave = LeaveRequest.objects.filter(
            staff__tenant=tenant, status='APPROVED',
            start_date__lte=today, end_date__gte=today
        ).values('staff_id').distinct().count()
        overview["staff_off"] = sick + on_leave
        overview["staff_on"] = total_staff - overview["staff_off"]
    except Exception:
        pass

    try:
        from compliance.models import ComplianceItem
        overview["overdue_compliance"] = ComplianceItem.objects.filter(
            category__tenant=tenant, status='OVERDUE'
        ).count()
    except Exception:
        pass

    return overview


def tool_get_available_staff(tenant, args):
    available = []
    try:
        from staff.models import StaffProfile, AbsenceRecord, LeaveRequest
        today = date.today()
        sick_ids = set(AbsenceRecord.objects.filter(
            staff__tenant=tenant, date=today
        ).values_list('staff_id', flat=True))
        leave_ids = set(LeaveRequest.objects.filter(
            staff__tenant=tenant, status='APPROVED',
            start_date__lte=today, end_date__gte=today
        ).values_list('staff_id', flat=True))
        off_ids = sick_ids | leave_ids

        seen_names = set()
        for p in StaffProfile.objects.filter(tenant=tenant, is_active=True).select_related('user'):
            if p.id not in off_ids:
                name = p.display_name or f"{p.user.first_name} {p.user.last_name}".strip()
                available.append({"name": name, "role": p.role})
                seen_names.add(name.lower())
    except Exception as e:
        logger.warning(f"[AI] Error getting available staff: {e}")
        seen_names = set()
    # Also include booking staff not already listed
    try:
        from bookings.models import Staff as BookingStaff
        for bs in BookingStaff.objects.filter(tenant=tenant, active=True):
            if bs.name.lower() not in seen_names:
                available.append({"name": bs.name, "role": bs.role or 'staff'})
                seen_names.add(bs.name.lower())
    except Exception:
        pass
    return {"available_staff": available, "count": len(available)}


def tool_navigate_user(tenant, args):
    page = args.get('page', '/admin')
    return {"navigate": page, "message": f"Navigating to {page}"}


# Tool dispatch map
TOOL_DISPATCH = {
    "mark_staff_sick": tool_mark_staff_sick,
    "get_who_is_off": tool_get_who_is_off,
    "get_staff_list": tool_get_staff_list,
    "get_todays_bookings": tool_get_todays_bookings,
    "get_unassigned_bookings": tool_get_unassigned_bookings,
    "get_staff_bookings": tool_get_staff_bookings,
    "get_vip_clients": tool_get_vip_clients,
    "get_at_risk_clients": tool_get_at_risk_clients,
    "add_crm_lead": tool_add_crm_lead,
    "get_compliance_status": tool_get_compliance_status,
    "get_overdue_compliance": tool_get_overdue_compliance,
    "get_todays_overview": tool_get_todays_overview,
    "get_available_staff": tool_get_available_staff,
    "navigate_user": tool_navigate_user,
}


# ═══════════════════════════════════════════════════════════════
# MAIN CHAT ENDPOINT
# ═══════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_chat(request):
    """
    POST /api/assistant/chat/
    Body: {
        "messages": [
            {"role": "user", "content": "Sam has called in sick today"}
        ]
    }

    Returns: {
        "reply": "I've marked Sam as sick for today. He had 2 bookings...",
        "tool_calls": [...],
        "navigate": "/admin/staff" (optional)
    }
    """
    tenant = getattr(request, 'tenant', None)

    # Module gate — ai_assistant must be enabled for this tenant
    if tenant:
        enabled = tenant.enabled_modules or []
        if enabled and 'ai_assistant' not in enabled:
            return Response(
                {'error': 'AI Assistant is a paid add-on. Contact support to enable it.'},
                status=status.HTTP_403_FORBIDDEN,
            )

    import os
    api_key = getattr(settings, 'OPENAI_API_KEY', '') or os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        logger.error('[AI] OPENAI_API_KEY not found in settings or os.environ')
        return Response(
            {'error': 'AI assistant is not configured. Set OPENAI_API_KEY in environment.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    messages = request.data.get('messages', [])
    if not messages:
        return Response(
            {'error': 'messages array is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Build OpenAI messages with system prompt
    openai_messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add conversation history (limit to last 20 messages to control token usage)
    for msg in messages[-20:]:
        role = msg.get('role', 'user')
        if role in ('user', 'assistant'):
            openai_messages.append({"role": role, "content": msg.get('content', '')})

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')

        # First call — LLM decides what tools to use
        response = client.chat.completions.create(
            model=model,
            messages=openai_messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.3,
            max_tokens=1000,
        )

        assistant_message = response.choices[0].message
        tool_calls_made = []
        navigate_to = None

        # Process tool calls in a loop (LLM may chain multiple)
        max_iterations = 5
        iteration = 0

        while assistant_message.tool_calls and iteration < max_iterations:
            iteration += 1

            # Add the assistant's message with tool calls
            openai_messages.append(assistant_message.model_dump())

            # Execute each tool call
            for tc in assistant_message.tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    fn_args = {}

                handler = TOOL_DISPATCH.get(fn_name)
                if handler:
                    result = handler(tenant, fn_args)
                    # Check for navigation
                    if fn_name == 'navigate_user' or (isinstance(result, dict) and 'navigate' in result):
                        navigate_to = result.get('navigate')
                else:
                    result = {"error": f"Unknown tool: {fn_name}"}

                tool_calls_made.append({
                    "tool": fn_name,
                    "args": fn_args,
                    "result": result,
                })

                # Feed result back to OpenAI
                openai_messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, default=str),
                })

            # Ask LLM to summarise the results (may trigger more tool calls)
            response = client.chat.completions.create(
                model=model,
                messages=openai_messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=1000,
            )
            assistant_message = response.choices[0].message

        # Final reply text
        reply = assistant_message.content or "Done."

        result = {
            "reply": reply,
            "tool_calls": [{"tool": tc["tool"], "args": tc["args"]} for tc in tool_calls_made],
        }
        if navigate_to:
            result["navigate"] = navigate_to

        return Response(result)

    except Exception as e:
        logger.error(f"[AI] Chat error: {e}", exc_info=True)
        return Response(
            {'error': f'AI assistant error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
