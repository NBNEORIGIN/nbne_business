"""
Dynamic staff-aware slot generation with double-booking prevention.

Ported from nbne-booking-instances (House of Hair / Mind Department) and
enhanced to use the main platform's WorkingHours + LeaveRequest models.
"""
from datetime import datetime, timedelta, time as dt_time, date as dt_date
from django.utils import timezone
from .models import Booking


def generate_staff_slots(staff_user_id, service_id, date_str, slot_interval_minutes=15):
    """
    Generate available time slots for a staff member on a given date.

    Uses the staff member's WorkingHours for that day-of-week, checks for
    approved leave, then removes any slots that overlap with existing bookings.

    Args:
        staff_user_id: User ID of the staff member
        service_id: Service ID (for duration)
        date_str: Date string YYYY-MM-DD
        slot_interval_minutes: Gap between slot start times (default 15)

    Returns:
        list of dicts: [{'start_time': 'HH:MM', 'end_time': 'HH:MM', 'available': True/False}]
    """
    from .models import Service

    try:
        service = Service.objects.get(id=service_id, is_active=True)
    except Service.DoesNotExist:
        return []

    target_date = dt_date.fromisoformat(date_str)

    # Don't generate slots for past dates
    if target_date < timezone.now().date():
        return []

    # Get staff working hours for this day of week
    day_of_week = target_date.weekday()  # 0=Monday
    working_periods = _get_working_periods(staff_user_id, day_of_week)

    if not working_periods:
        return []

    # Check if staff is on approved leave
    if _is_on_leave(staff_user_id, target_date):
        return []

    # Get existing bookings for this staff on this date (non-cancelled)
    existing_bookings = _get_existing_bookings(staff_user_id, target_date)

    # Generate slots within each working period
    duration = timedelta(minutes=service.duration_minutes)
    interval = timedelta(minutes=slot_interval_minutes)
    slots = []

    for period_start, period_end in working_periods:
        current = datetime.combine(target_date, period_start)
        end_boundary = datetime.combine(target_date, period_end)

        while current + duration <= end_boundary:
            slot_end = current + duration

            # Check overlap with existing bookings
            is_available = True
            for bk_start, bk_end in existing_bookings:
                if current < bk_end and slot_end > bk_start:
                    is_available = False
                    break

            # For today, skip slots that have already passed
            if target_date == timezone.now().date():
                now_naive = timezone.now().replace(tzinfo=None)
                if hasattr(timezone.now(), 'astimezone'):
                    now_naive = timezone.localtime(timezone.now()).replace(tzinfo=None)
                if current < now_naive:
                    is_available = False

            if is_available:
                slots.append({
                    'start_time': current.strftime('%H:%M'),
                    'end_time': slot_end.strftime('%H:%M'),
                    'available': True,
                })

            current += interval

    return slots


def get_bookable_staff(service_id):
    """
    Return a list of active staff members who can be booked.
    For now, returns all active staff with StaffProfiles.
    Future: filter by staff-service M2M if configured.

    Returns:
        list of dicts: [{'user_id': int, 'display_name': str}]
    """
    try:
        from staff.models import StaffProfile
        profiles = StaffProfile.objects.filter(is_active=True).select_related('user')
        return [
            {
                'user_id': p.user_id,
                'display_name': p.display_name,
            }
            for p in profiles
        ]
    except Exception:
        return []


def _get_working_periods(staff_user_id, day_of_week):
    """
    Get working time periods for a staff member on a given day of week.
    Returns list of (start_time, end_time) tuples.
    Falls back to default business hours (09:00-17:00) if no WorkingHours configured.
    """
    try:
        from staff.models import StaffProfile, WorkingHours
        profile = StaffProfile.objects.get(user_id=staff_user_id, is_active=True)
        hours = WorkingHours.objects.filter(
            staff=profile, day_of_week=day_of_week, is_active=True
        ).order_by('start_time')

        if hours.exists():
            return [(h.start_time, h.end_time) for h in hours]

        # No working hours configured — use default 09:00-17:00
        return [(dt_time(9, 0), dt_time(17, 0))]
    except Exception:
        # Staff module not available or profile not found — use defaults
        return [(dt_time(9, 0), dt_time(17, 0))]


def _is_on_leave(staff_user_id, target_date):
    """Check if staff member has approved leave on this date."""
    try:
        from staff.models import StaffProfile, LeaveRequest
        profile = StaffProfile.objects.get(user_id=staff_user_id)
        return LeaveRequest.objects.filter(
            staff=profile,
            status='APPROVED',
            start_date__lte=target_date,
            end_date__gte=target_date,
        ).exists()
    except Exception:
        return False


def _get_existing_bookings(staff_user_id, target_date):
    """
    Get existing non-cancelled bookings for a staff member on a date.
    Returns list of (start_datetime, end_datetime) tuples.
    Handles both legacy TimeSlot bookings and staff-aware direct bookings.
    """
    from django.db.models import Q

    bookings = Booking.objects.filter(
        assigned_staff_id=staff_user_id,
    ).filter(
        Q(time_slot__date=target_date) | Q(booking_date=target_date)
    ).exclude(
        status__in=['CANCELLED', 'NO_SHOW']
    ).select_related('time_slot', 'service')

    result = []
    for b in bookings:
        if b.time_slot:
            start = datetime.combine(target_date, b.time_slot.start_time)
            end = datetime.combine(target_date, b.time_slot.end_time)
        elif b.booking_date and b.booking_time:
            start = datetime.combine(target_date, b.booking_time)
            end = start + timedelta(minutes=b.service.duration_minutes)
        else:
            continue
        result.append((start, end))

    return result
