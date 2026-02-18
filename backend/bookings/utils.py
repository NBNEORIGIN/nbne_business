from datetime import datetime, timedelta
from django.utils import timezone
from .models import Booking, Staff, Service, StaffBlock


def generate_time_slots(staff_id, service_id, date, business_hours_start=9, business_hours_end=17):
    """
    Generate available time slots for a given staff member, service, and date.
    Excludes slots that overlap with existing bookings or staff blocks.
    """
    try:
        staff = Staff.objects.get(id=staff_id, active=True)
        service = Service.objects.get(id=service_id, active=True)
    except (Staff.DoesNotExist, Service.DoesNotExist):
        return []
    
    # Parse date
    target_date = datetime.strptime(date, '%Y-%m-%d').date()
    
    # Get existing bookings for this staff on this date
    start_of_day = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
    end_of_day = timezone.make_aware(datetime.combine(target_date, datetime.max.time()))
    
    existing_bookings = Booking.objects.filter(
        staff=staff,
        start_time__gte=start_of_day,
        start_time__lt=end_of_day,
        status__in=['pending', 'confirmed']
    ).order_by('start_time')
    
    # Get staff blocks for this date
    staff_blocks = StaffBlock.objects.filter(staff=staff, date=target_date)
    
    # If any block is all_day, no slots available
    if staff_blocks.filter(all_day=True).exists():
        return []
    
    # Generate potential slots
    slots = []
    current_time = timezone.make_aware(
        datetime.combine(target_date, datetime.min.time().replace(hour=business_hours_start))
    )
    end_time = timezone.make_aware(
        datetime.combine(target_date, datetime.min.time().replace(hour=business_hours_end))
    )
    
    slot_duration = timedelta(minutes=service.duration_minutes)
    
    while current_time + slot_duration <= end_time:
        slot_end = current_time + slot_duration
        
        # Check if this slot conflicts with existing bookings
        is_available = True
        for booking in existing_bookings:
            if (current_time < booking.end_time and slot_end > booking.start_time):
                is_available = False
                break
        
        # Check if this slot conflicts with staff blocks
        if is_available:
            slot_start_time = current_time.time()
            slot_end_time = slot_end.time()
            for block in staff_blocks:
                if slot_start_time < block.end_time and slot_end_time > block.start_time:
                    is_available = False
                    break
        
        # Check if this slot conflicts with staff's recurring daily break
        if is_available and staff.break_start and staff.break_end:
            slot_start_time = current_time.time()
            slot_end_time = slot_end.time()
            if slot_start_time < staff.break_end and slot_end_time > staff.break_start:
                is_available = False
        
        if is_available:
            slots.append({
                'start_time': current_time.strftime('%H:%M'),
                'end_time': slot_end.strftime('%H:%M'),
                'available': True
            })
        
        # Move to next slot (15-minute intervals)
        current_time += timedelta(minutes=15)
    
    return slots


def get_available_dates(staff_id, service_id, days_ahead=30):
    """
    Get list of dates with available slots for the next N days.
    
    Args:
        staff_id: Staff member ID
        service_id: Service ID
        days_ahead: Number of days to look ahead (default 30)
    
    Returns:
        List of dates with at least one available slot
    """
    available_dates = []
    today = datetime.now().date()
    
    for day_offset in range(days_ahead):
        check_date = today + timedelta(days=day_offset)
        date_str = check_date.strftime('%Y-%m-%d')
        
        slots = generate_time_slots(staff_id, service_id, date_str)
        if slots:
            available_dates.append({
                'date': date_str,
                'available_slots': len(slots)
            })
    
    return available_dates
