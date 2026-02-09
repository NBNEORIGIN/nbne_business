import secrets
import string
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import transaction
from accounts.models import User
from accounts.permissions import IsStaffOrAbove, IsManagerOrAbove, IsOwner
from .models import StaffProfile, Shift, LeaveRequest, TrainingRecord, AbsenceRecord, WorkingHours, TimesheetEntry
from .serializers import (
    StaffProfileSerializer, ShiftSerializer, ShiftCreateSerializer,
    LeaveRequestSerializer, LeaveCreateSerializer, LeaveReviewSerializer,
    TrainingRecordSerializer, TrainingCreateSerializer,
    AbsenceRecordSerializer, AbsenceCreateSerializer,
    WorkingHoursSerializer, WorkingHoursCreateSerializer,
    TimesheetEntrySerializer, TimesheetUpdateSerializer,
)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def staff_list(request):
    """List all staff profiles (staff+). Only active by default, ?include_inactive=true for all."""
    profiles = StaffProfile.objects.select_related('user').all()
    if request.query_params.get('include_inactive') != 'true':
        profiles = profiles.filter(is_active=True)
    return Response(StaffProfileSerializer(profiles, many=True).data)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def staff_detail(request, staff_id):
    try:
        profile = StaffProfile.objects.select_related('user').get(id=staff_id)
    except StaffProfile.DoesNotExist:
        return Response({'error': 'Staff not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(StaffProfileSerializer(profile).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def staff_create(request):
    """Create a new staff member (User + StaffProfile). Manager+ only."""
    first_name = request.data.get('first_name', '').strip()
    last_name = request.data.get('last_name', '').strip()
    email = request.data.get('email', '').strip()
    phone = request.data.get('phone', '').strip()
    role = request.data.get('role', 'staff')
    # Generate a random temporary password
    alphabet = string.ascii_letters + string.digits
    temp_password = ''.join(secrets.choice(alphabet) for _ in range(10))

    if not first_name or not last_name:
        return Response({'error': 'First name and last name are required.'}, status=status.HTTP_400_BAD_REQUEST)
    if not email:
        return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
    if role not in ('staff', 'manager'):
        return Response({'error': 'Role must be staff or manager.'}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(email=email).exists():
        return Response({'error': 'A user with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    username = email.split('@')[0].lower().replace('.', '_')
    base_username = username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f'{base_username}_{counter}'
        counter += 1

    with transaction.atomic():
        user = User.objects.create_user(
            username=username, email=email, password=temp_password,
            first_name=first_name, last_name=last_name,
            role=role, is_staff=(role in ('manager', 'owner')),
        )
        user.must_change_password = True
        user.save(update_fields=['must_change_password'])
        profile = StaffProfile.objects.create(
            user=user,
            display_name=f'{first_name} {last_name}',
            phone=phone,
            hire_date=timezone.now().date(),
        )
        # Auto-add to all active team chat channels (not DMs)
        try:
            from comms.models import Channel
            channels = Channel.objects.filter(is_archived=False).exclude(channel_type='DIRECT')
            for ch in channels:
                ch.members.add(user)
        except Exception:
            pass  # comms module may not be enabled
    # Send welcome email with temp credentials
    try:
        from .emails import send_welcome_email
        origin = request.META.get('HTTP_ORIGIN', request.META.get('HTTP_REFERER', ''))
        # Strip path from origin/referer to get base URL
        if '/' in origin.split('//')[1] if '//' in origin else False:
            origin = origin.split('//')[0] + '//' + origin.split('//')[1].split('/')[0]
        login_url = f'{origin}/login' if origin else 'https://app.nbnesigns.co.uk/login'
        send_welcome_email(user, temp_password, login_url)
    except Exception:
        pass  # email sending is best-effort
    data = StaffProfileSerializer(profile).data
    data['temp_password'] = temp_password
    data['username'] = username
    return Response(data, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsManagerOrAbove])
def staff_update(request, staff_id):
    """Update a staff member's details. Manager+ only."""
    try:
        profile = StaffProfile.objects.select_related('user').get(id=staff_id)
    except StaffProfile.DoesNotExist:
        return Response({'error': 'Staff not found'}, status=status.HTTP_404_NOT_FOUND)

    user = profile.user
    data = request.data

    if 'first_name' in data:
        user.first_name = data['first_name'].strip()
    if 'last_name' in data:
        user.last_name = data['last_name'].strip()
    if 'email' in data:
        new_email = data['email'].strip()
        if new_email != user.email and User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
            return Response({'error': 'A user with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        user.email = new_email
    if 'role' in data and data['role'] in ('staff', 'manager'):
        user.role = data['role']
        user.is_staff = data['role'] in ('manager', 'owner')
    if 'phone' in data:
        profile.phone = data['phone'].strip()
    if 'emergency_contact_name' in data:
        profile.emergency_contact_name = data['emergency_contact_name'].strip()
    if 'emergency_contact_phone' in data:
        profile.emergency_contact_phone = data['emergency_contact_phone'].strip()
    if 'notes' in data:
        profile.notes = data['notes']

    # Update display name if name fields changed
    if 'first_name' in data or 'last_name' in data:
        profile.display_name = f'{user.first_name} {user.last_name}'

    user.save()
    profile.save()
    return Response(StaffProfileSerializer(profile).data)


@api_view(['DELETE'])
@permission_classes([IsManagerOrAbove])
def staff_delete(request, staff_id):
    """Deactivate a staff member. Manager+ only."""
    try:
        profile = StaffProfile.objects.select_related('user').get(id=staff_id)
    except StaffProfile.DoesNotExist:
        return Response({'error': 'Staff not found'}, status=status.HTTP_404_NOT_FOUND)
    if profile.user.role == 'owner':
        return Response({'error': 'Cannot deactivate an owner account.'}, status=status.HTTP_400_BAD_REQUEST)
    profile.is_active = False
    profile.save(update_fields=['is_active', 'updated_at'])
    profile.user.is_active = False
    profile.user.save(update_fields=['is_active'])
    return Response({'detail': 'Staff member deactivated.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def my_shifts(request):
    """Get current user's shifts."""
    try:
        profile = request.user.staff_profile
    except StaffProfile.DoesNotExist:
        return Response([])
    shifts = Shift.objects.filter(staff=profile, date__gte=timezone.now().date()).select_related('staff')
    return Response(ShiftSerializer(shifts, many=True).data)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def shift_list(request):
    """List all shifts (staff+). Supports ?staff_id= and ?date= filters."""
    shifts = Shift.objects.select_related('staff').all()
    staff_id = request.query_params.get('staff_id')
    if staff_id:
        shifts = shifts.filter(staff_id=staff_id)
    date = request.query_params.get('date')
    if date:
        shifts = shifts.filter(date=date)
    return Response(ShiftSerializer(shifts, many=True).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def shift_create(request):
    """Create a shift (manager+)."""
    serializer = ShiftCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    shift = serializer.save()
    return Response(ShiftSerializer(shift).data, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsManagerOrAbove])
def shift_update(request, shift_id):
    """Update a shift (manager+)."""
    try:
        shift = Shift.objects.get(id=shift_id)
    except Shift.DoesNotExist:
        return Response({'error': 'Shift not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = ShiftCreateSerializer(shift, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(ShiftSerializer(shift).data)


@api_view(['DELETE'])
@permission_classes([IsManagerOrAbove])
def shift_delete(request, shift_id):
    """Delete a shift (manager+)."""
    try:
        shift = Shift.objects.get(id=shift_id)
    except Shift.DoesNotExist:
        return Response({'error': 'Shift not found'}, status=status.HTTP_404_NOT_FOUND)
    shift.delete()
    return Response({'detail': 'Shift deleted.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def leave_list(request):
    """List leave requests (staff+). Staff see own, managers see all."""
    leaves = LeaveRequest.objects.select_related('staff', 'reviewed_by').all()
    if not request.user.is_manager_or_above:
        try:
            profile = request.user.staff_profile
            leaves = leaves.filter(staff=profile)
        except StaffProfile.DoesNotExist:
            return Response([])
    status_filter = request.query_params.get('status')
    if status_filter:
        leaves = leaves.filter(status=status_filter)
    return Response(LeaveRequestSerializer(leaves, many=True).data)


@api_view(['POST'])
@permission_classes([IsStaffOrAbove])
def leave_create(request):
    """Create a leave request (staff+)."""
    serializer = LeaveCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    leave = serializer.save()
    return Response(LeaveRequestSerializer(leave).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def leave_review(request, leave_id):
    """Approve or reject a leave request (manager+)."""
    try:
        leave = LeaveRequest.objects.get(id=leave_id)
    except LeaveRequest.DoesNotExist:
        return Response({'error': 'Leave request not found'}, status=status.HTTP_404_NOT_FOUND)
    if leave.status != 'PENDING':
        return Response({'error': 'Only pending requests can be reviewed.'}, status=status.HTTP_400_BAD_REQUEST)
    serializer = LeaveReviewSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    leave.status = serializer.validated_data['status']
    try:
        leave.reviewed_by = request.user.staff_profile
    except StaffProfile.DoesNotExist:
        pass
    leave.reviewed_at = timezone.now()
    leave.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])
    return Response(LeaveRequestSerializer(leave).data)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def training_list(request):
    """List training records (staff+)."""
    records = TrainingRecord.objects.select_related('staff').all()
    if not request.user.is_manager_or_above:
        try:
            profile = request.user.staff_profile
            records = records.filter(staff=profile)
        except StaffProfile.DoesNotExist:
            return Response([])
    return Response(TrainingRecordSerializer(records, many=True).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def training_create(request):
    """Create a training record (manager+)."""
    serializer = TrainingCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    record = serializer.save()
    return Response(TrainingRecordSerializer(record).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def absence_list(request):
    """List absence records (manager+)."""
    records = AbsenceRecord.objects.select_related('staff').all()
    staff_id = request.query_params.get('staff_id')
    if staff_id:
        records = records.filter(staff_id=staff_id)
    return Response(AbsenceRecordSerializer(records, many=True).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def absence_create(request):
    """Create an absence record (manager+)."""
    serializer = AbsenceCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    record = serializer.save()
    return Response(AbsenceRecordSerializer(record).data, status=status.HTTP_201_CREATED)


# ── Working Hours ────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def working_hours_list(request):
    """List working hours. ?staff_id= to filter by staff."""
    qs = WorkingHours.objects.select_related('staff').filter(is_active=True)
    staff_id = request.query_params.get('staff_id')
    if staff_id:
        qs = qs.filter(staff_id=staff_id)
    return Response(WorkingHoursSerializer(qs, many=True).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def working_hours_create(request):
    """Create a working hours entry (manager+)."""
    serializer = WorkingHoursCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    wh = serializer.save()
    return Response(WorkingHoursSerializer(wh).data, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsManagerOrAbove])
def working_hours_update(request, wh_id):
    """Update a working hours entry (manager+)."""
    try:
        wh = WorkingHours.objects.get(id=wh_id)
    except WorkingHours.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = WorkingHoursCreateSerializer(wh, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(WorkingHoursSerializer(wh).data)


@api_view(['DELETE'])
@permission_classes([IsManagerOrAbove])
def working_hours_delete(request, wh_id):
    """Delete a working hours entry (manager+)."""
    try:
        wh = WorkingHours.objects.get(id=wh_id)
    except WorkingHours.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    wh.delete()
    return Response({'detail': 'Deleted.'})


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def working_hours_bulk_set(request):
    """Bulk set working hours for a staff member. Replaces all existing entries.
    Expects: { staff: <id>, hours: [ { day_of_week, start_time, end_time, break_minutes }, ... ] }
    """
    staff_id = request.data.get('staff')
    hours = request.data.get('hours', [])
    if not staff_id:
        return Response({'error': 'staff is required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        profile = StaffProfile.objects.get(id=staff_id)
    except StaffProfile.DoesNotExist:
        return Response({'error': 'Staff not found'}, status=status.HTTP_404_NOT_FOUND)
    with transaction.atomic():
        WorkingHours.objects.filter(staff=profile).delete()
        created = []
        for h in hours:
            wh = WorkingHours.objects.create(
                staff=profile,
                day_of_week=h['day_of_week'],
                start_time=h['start_time'],
                end_time=h['end_time'],
                break_minutes=h.get('break_minutes', 0),
            )
            created.append(wh)
    return Response(WorkingHoursSerializer(created, many=True).data, status=status.HTTP_201_CREATED)


# ── Timesheets ───────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def timesheet_list(request):
    """List timesheet entries. ?staff_id=, ?date_from=, ?date_to= filters.
    Staff see own only; managers see all."""
    qs = TimesheetEntry.objects.select_related('staff').all()
    if not request.user.is_manager_or_above:
        try:
            profile = request.user.staff_profile
            qs = qs.filter(staff=profile)
        except StaffProfile.DoesNotExist:
            return Response([])
    staff_id = request.query_params.get('staff_id')
    if staff_id:
        qs = qs.filter(staff_id=staff_id)
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)
    return Response(TimesheetEntrySerializer(qs, many=True).data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsManagerOrAbove])
def timesheet_update(request, ts_id):
    """Update a timesheet entry (actual times, status, notes). Manager+."""
    try:
        entry = TimesheetEntry.objects.get(id=ts_id)
    except TimesheetEntry.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = TimesheetUpdateSerializer(entry, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(TimesheetEntrySerializer(entry).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def timesheet_generate(request):
    """Auto-populate timesheets from working hours for a date range.
    Expects: { date_from: 'YYYY-MM-DD', date_to: 'YYYY-MM-DD', staff_id?: <id> }
    Skips dates that already have entries. Creates SCHEDULED entries from WorkingHours.
    """
    from datetime import datetime, timedelta
    date_from_str = request.data.get('date_from')
    date_to_str = request.data.get('date_to')
    if not date_from_str or not date_to_str:
        return Response({'error': 'date_from and date_to are required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)
    if date_to < date_from:
        return Response({'error': 'date_to must be >= date_from'}, status=status.HTTP_400_BAD_REQUEST)
    if (date_to - date_from).days > 90:
        return Response({'error': 'Max 90 days at a time'}, status=status.HTTP_400_BAD_REQUEST)

    staff_filter = {}
    staff_id = request.data.get('staff_id')
    if staff_id:
        staff_filter['staff_id'] = staff_id

    all_wh = WorkingHours.objects.filter(is_active=True, **staff_filter).select_related('staff')
    # Group by staff
    wh_by_staff = {}
    for wh in all_wh:
        wh_by_staff.setdefault(wh.staff_id, []).append(wh)

    created_count = 0
    current = date_from
    while current <= date_to:
        dow = current.weekday()  # 0=Monday
        for staff_id_key, wh_list in wh_by_staff.items():
            day_entries = [w for w in wh_list if w.day_of_week == dow]
            if not day_entries:
                continue
            # Use the first entry for this day (primary shift)
            wh = day_entries[0]
            # Combine all segments: earliest start, latest end, sum breaks
            earliest_start = min(w.start_time for w in day_entries)
            latest_end = max(w.end_time for w in day_entries)
            total_break = sum(w.break_minutes for w in day_entries)
            # Calculate gap between segments as additional break
            if len(day_entries) > 1:
                sorted_entries = sorted(day_entries, key=lambda w: w.start_time)
                for i in range(len(sorted_entries) - 1):
                    gap_start = datetime.combine(current, sorted_entries[i].end_time)
                    gap_end = datetime.combine(current, sorted_entries[i + 1].start_time)
                    if gap_end > gap_start:
                        total_break += int((gap_end - gap_start).total_seconds() / 60)

            _, created = TimesheetEntry.objects.get_or_create(
                staff_id=staff_id_key, date=current,
                defaults={
                    'scheduled_start': earliest_start,
                    'scheduled_end': latest_end,
                    'scheduled_break_minutes': total_break,
                    'status': 'SCHEDULED',
                }
            )
            if created:
                created_count += 1
        current += timedelta(days=1)

    return Response({'detail': f'{created_count} timesheet entries created.', 'created': created_count})


@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def timesheet_summary(request):
    """Aggregated timesheet summary for payroll dashboard.
    ?period=daily|weekly|monthly  ?date=YYYY-MM-DD  ?staff_id=
    Returns per-staff totals: scheduled_hours, actual_hours, variance, days_worked, absences.
    """
    from datetime import datetime, timedelta
    from django.db.models import Sum, Count, Q, F

    period = request.query_params.get('period', 'weekly')
    date_str = request.query_params.get('date')
    if date_str:
        try:
            ref_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        ref_date = timezone.now().date()

    if period == 'daily':
        date_from = ref_date
        date_to = ref_date
    elif period == 'monthly':
        date_from = ref_date.replace(day=1)
        next_month = (date_from.replace(day=28) + timedelta(days=4))
        date_to = next_month.replace(day=1) - timedelta(days=1)
    else:  # weekly
        date_from = ref_date - timedelta(days=ref_date.weekday())  # Monday
        date_to = date_from + timedelta(days=6)  # Sunday

    qs = TimesheetEntry.objects.filter(date__gte=date_from, date__lte=date_to)
    staff_id = request.query_params.get('staff_id')
    if staff_id:
        qs = qs.filter(staff_id=staff_id)

    entries = qs.select_related('staff')
    # Aggregate per staff
    summary = {}
    for e in entries:
        sid = e.staff_id
        if sid not in summary:
            summary[sid] = {
                'staff_id': sid,
                'staff_name': e.staff.display_name,
                'scheduled_hours': 0,
                'actual_hours': 0,
                'days_worked': 0,
                'days_absent': 0,
                'days_sick': 0,
                'days_holiday': 0,
                'entries': [],
            }
        s = summary[sid]
        s['scheduled_hours'] += e.scheduled_hours
        s['actual_hours'] += e.actual_hours
        if e.status == 'WORKED' or e.status == 'LATE' or e.status == 'LEFT_EARLY' or e.status == 'AMENDED':
            s['days_worked'] += 1
        elif e.status == 'ABSENT':
            s['days_absent'] += 1
        elif e.status == 'SICK':
            s['days_sick'] += 1
        elif e.status == 'HOLIDAY':
            s['days_holiday'] += 1
        s['entries'].append(TimesheetEntrySerializer(e).data)

    for s in summary.values():
        s['scheduled_hours'] = round(s['scheduled_hours'], 2)
        s['actual_hours'] = round(s['actual_hours'], 2)
        s['variance_hours'] = round(s['actual_hours'] - s['scheduled_hours'], 2)

    return Response({
        'period': period,
        'date_from': str(date_from),
        'date_to': str(date_to),
        'staff_summaries': list(summary.values()),
    })
