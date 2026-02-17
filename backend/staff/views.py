import secrets
import string
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import transaction
from accounts.models import User
from accounts.permissions import IsStaffOrAbove, IsManagerOrAbove, IsOwner
from .models import StaffProfile, Shift, LeaveRequest, TrainingCourse, TrainingRecord, AbsenceRecord, WorkingHours, TimesheetEntry, ProjectCode
from .serializers import (
    StaffProfileSerializer, ShiftSerializer, ShiftCreateSerializer,
    LeaveRequestSerializer, LeaveCreateSerializer, LeaveReviewSerializer,
    TrainingCourseSerializer, TrainingCourseCreateSerializer,
    TrainingRecordSerializer, TrainingCreateSerializer,
    AbsenceRecordSerializer, AbsenceCreateSerializer,
    WorkingHoursSerializer, WorkingHoursCreateSerializer,
    TimesheetEntrySerializer, TimesheetUpdateSerializer,
    ProjectCodeSerializer, ProjectCodeCreateSerializer,
)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def staff_list(request):
    """List all staff profiles (staff+). Only active by default, ?include_inactive=true for all."""
    tenant = getattr(request, 'tenant', None)
    profiles = StaffProfile.objects.select_related('user').filter(tenant=tenant)
    if request.query_params.get('include_inactive') != 'true':
        profiles = profiles.filter(is_active=True)
    return Response(StaffProfileSerializer(profiles, many=True).data)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def staff_detail(request, staff_id):
    try:
        tenant = getattr(request, 'tenant', None)
        profile = StaffProfile.objects.select_related('user').get(id=staff_id, tenant=tenant)
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
    if role not in ('staff', 'manager', 'owner'):
        return Response({'error': 'Role must be staff, manager, or owner.'}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(email=email).exists():
        return Response({'error': 'A user with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    username = email.split('@')[0].lower().replace('.', '_')
    base_username = username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f'{base_username}_{counter}'
        counter += 1

    tenant = getattr(request, 'tenant', None)
    with transaction.atomic():
        user = User.objects.create_user(
            username=username, email=email, password=temp_password,
            first_name=first_name, last_name=last_name,
            role=role, is_staff=(role in ('manager', 'owner')),
        )
        user.tenant = tenant
        user.must_change_password = True
        user.save(update_fields=['must_change_password', 'tenant'])
        profile = StaffProfile.objects.create(
            user=user,
            tenant=tenant,
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
        tenant = getattr(request, 'tenant', None)
        profile = StaffProfile.objects.select_related('user').get(id=staff_id, tenant=tenant)
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
    if 'role' in data and data['role'] in ('staff', 'manager', 'owner'):
        user.role = data['role']
        user.is_staff = data['role'] in ('manager', 'owner')
        user.is_superuser = data['role'] == 'owner'
    if 'phone' in data:
        profile.phone = data['phone'].strip()
    if 'emergency_contact_name' in data:
        profile.emergency_contact_name = data['emergency_contact_name'].strip()
    if 'emergency_contact_phone' in data:
        profile.emergency_contact_phone = data['emergency_contact_phone'].strip()
    if 'notes' in data:
        profile.notes = data['notes']
    # Payroll & hours fields
    if 'pay_type' in data and data['pay_type'] in ('salaried', 'hourly'):
        profile.pay_type = data['pay_type']
    if 'overtime_eligible' in data:
        profile.overtime_eligible = bool(data['overtime_eligible'])
    if 'contracted_hours_per_week' in data:
        profile.contracted_hours_per_week = data['contracted_hours_per_week']
    if 'hourly_rate' in data:
        profile.hourly_rate = data['hourly_rate']
    if 'annual_leave_days' in data:
        profile.annual_leave_days = data['annual_leave_days']

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
        tenant = getattr(request, 'tenant', None)
        profile = StaffProfile.objects.select_related('user').get(id=staff_id, tenant=tenant)
    except StaffProfile.DoesNotExist:
        return Response({'error': 'Staff not found'}, status=status.HTTP_404_NOT_FOUND)
    if profile.user.id == request.user.id:
        return Response({'error': 'Cannot deactivate your own account.'}, status=status.HTTP_400_BAD_REQUEST)
    profile.is_active = False
    profile.save(update_fields=['is_active', 'updated_at'])
    profile.user.is_active = False
    profile.user.save(update_fields=['is_active'])
    return Response({'detail': 'Staff member deactivated.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsOwner])
def staff_purge(request):
    """Hard-delete a user by email. Owner only. Use when a user was partially created."""
    email = request.data.get('email', '').strip()
    if not email:
        return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
    tenant = getattr(request, 'tenant', None)
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'error': f'No user found with email: {email}'}, status=status.HTTP_404_NOT_FOUND)
    if user.id == request.user.id:
        return Response({'error': 'Cannot delete your own account.'}, status=status.HTTP_400_BAD_REQUEST)
    name = f'{user.first_name} {user.last_name}'.strip() or user.username
    user.delete()
    return Response({'detail': f'User "{name}" ({email}) permanently deleted.'})


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
    tenant = getattr(request, 'tenant', None)
    shifts = Shift.objects.select_related('staff').filter(staff__tenant=tenant)
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
        tenant = getattr(request, 'tenant', None)
        shift = Shift.objects.get(id=shift_id, staff__tenant=tenant)
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
        tenant = getattr(request, 'tenant', None)
        shift = Shift.objects.get(id=shift_id, staff__tenant=tenant)
    except Shift.DoesNotExist:
        return Response({'error': 'Shift not found'}, status=status.HTTP_404_NOT_FOUND)
    shift.delete()
    return Response({'detail': 'Shift deleted.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def leave_list(request):
    """List leave requests (staff+). Staff see own, managers see all."""
    tenant = getattr(request, 'tenant', None)
    leaves = LeaveRequest.objects.select_related('staff', 'reviewed_by').filter(staff__tenant=tenant)
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


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def leave_calendar(request):
    """Return all approved + pending leave for a date range (all staff in tenant).
    Used by the calendar overlay so staff can see who's already off.
    ?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
    """
    tenant = getattr(request, 'tenant', None)
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    if not date_from or not date_to:
        return Response({'error': 'date_from and date_to are required'}, status=status.HTTP_400_BAD_REQUEST)
    qs = LeaveRequest.objects.select_related('staff').filter(
        staff__tenant=tenant,
        status__in=['APPROVED', 'PENDING'],
        start_date__lte=date_to,
        end_date__gte=date_from,
    )
    return Response(LeaveRequestSerializer(qs, many=True).data)


@api_view(['POST'])
@permission_classes([IsStaffOrAbove])
def leave_create(request):
    """Create a leave request (staff+). Max 12 months ahead."""
    from datetime import timedelta
    serializer = LeaveCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    tenant = getattr(request, 'tenant', None)
    start_date = serializer.validated_data['start_date']
    end_date = serializer.validated_data['end_date']
    # Validate: not in the past
    today = timezone.now().date()
    if start_date < today:
        return Response({'error': 'Cannot book leave in the past.'}, status=status.HTTP_400_BAD_REQUEST)
    # Validate: max 12 months ahead
    max_date = today + timedelta(days=365)
    if end_date > max_date:
        return Response({'error': 'Cannot book leave more than 12 months in advance.'}, status=status.HTTP_400_BAD_REQUEST)
    if end_date < start_date:
        return Response({'error': 'End date must be on or after start date.'}, status=status.HTTP_400_BAD_REQUEST)
    staff_id = serializer.validated_data.get('staff', getattr(serializer.validated_data.get('staff'), 'id', None))
    if staff_id and not StaffProfile.objects.filter(id=staff_id if isinstance(staff_id, int) else staff_id.id, tenant=tenant).exists():
        return Response({'error': 'Staff not found'}, status=status.HTTP_404_NOT_FOUND)
    leave = serializer.save()
    return Response(LeaveRequestSerializer(leave).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def leave_review(request, leave_id):
    """Approve or reject a leave request (manager+)."""
    try:
        tenant = getattr(request, 'tenant', None)
        leave = LeaveRequest.objects.get(id=leave_id, staff__tenant=tenant)
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
    # Send email notification to the staff member
    try:
        from .emails import send_leave_decision_email
        origin = request.META.get('HTTP_ORIGIN', request.META.get('HTTP_REFERER', ''))
        if '//' in origin:
            origin = origin.split('//')[0] + '//' + origin.split('//')[1].split('/')[0]
        send_leave_decision_email(leave, origin)
    except Exception:
        pass  # email is best-effort
    return Response(LeaveRequestSerializer(leave).data)


@api_view(['DELETE'])
@permission_classes([IsManagerOrAbove])
def leave_delete(request, leave_id):
    """Delete a leave request (manager+)."""
    try:
        tenant = getattr(request, 'tenant', None)
        leave = LeaveRequest.objects.get(id=leave_id, staff__tenant=tenant)
    except LeaveRequest.DoesNotExist:
        return Response({'error': 'Leave request not found'}, status=status.HTTP_404_NOT_FOUND)
    leave.delete()
    return Response({'detail': 'Leave request deleted.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def training_list(request):
    """List training records (staff+)."""
    tenant = getattr(request, 'tenant', None)
    records = TrainingRecord.objects.select_related('staff', 'course').filter(staff__tenant=tenant)
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
    """Create a training record (manager+). If course is provided, auto-populate title/provider/expiry."""
    from dateutil.relativedelta import relativedelta
    data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
    tenant = getattr(request, 'tenant', None)
    # Auto-populate from course if provided
    course_id = data.get('course')
    if course_id:
        try:
            course = TrainingCourse.objects.get(id=course_id, tenant=tenant, is_active=True)
            if not data.get('title'):
                data['title'] = course.name
            if not data.get('provider'):
                data['provider'] = course.provider
            # Auto-calculate expiry from completed_date + renewal_months
            if not data.get('expiry_date') and data.get('completed_date') and course.renewal_months > 0:
                from datetime import date as dt_date
                completed = data['completed_date']
                if isinstance(completed, str):
                    completed = dt_date.fromisoformat(completed)
                data['expiry_date'] = str(completed + relativedelta(months=course.renewal_months))
        except TrainingCourse.DoesNotExist:
            pass
    serializer = TrainingCreateSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    staff_obj = serializer.validated_data.get('staff')
    if staff_obj and not StaffProfile.objects.filter(id=staff_obj.id, tenant=tenant).exists():
        return Response({'error': 'Staff not found'}, status=status.HTTP_404_NOT_FOUND)
    record = serializer.save()
    return Response(TrainingRecordSerializer(record).data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsManagerOrAbove])
def training_delete(request, record_id):
    """Delete a training record (manager+)."""
    try:
        tenant = getattr(request, 'tenant', None)
        record = TrainingRecord.objects.get(id=record_id, staff__tenant=tenant)
    except TrainingRecord.DoesNotExist:
        return Response({'error': 'Training record not found'}, status=status.HTTP_404_NOT_FOUND)
    record.delete()
    return Response({'detail': 'Training record deleted.'}, status=status.HTTP_200_OK)


# --- Training Courses ---

@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def training_course_list(request):
    """List training courses for this tenant."""
    tenant = getattr(request, 'tenant', None)
    courses = TrainingCourse.objects.filter(tenant=tenant, is_active=True)
    return Response(TrainingCourseSerializer(courses, many=True).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def training_course_create(request):
    """Create a training course (manager+)."""
    serializer = TrainingCourseCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    tenant = getattr(request, 'tenant', None)
    course = serializer.save(tenant=tenant)
    return Response(TrainingCourseSerializer(course).data, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
@permission_classes([IsManagerOrAbove])
def training_course_update(request, course_id):
    """Update a training course (manager+)."""
    try:
        tenant = getattr(request, 'tenant', None)
        course = TrainingCourse.objects.get(id=course_id, tenant=tenant)
    except TrainingCourse.DoesNotExist:
        return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = TrainingCourseCreateSerializer(course, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(TrainingCourseSerializer(course).data)


@api_view(['DELETE'])
@permission_classes([IsManagerOrAbove])
def training_course_delete(request, course_id):
    """Soft-delete a training course (manager+)."""
    try:
        tenant = getattr(request, 'tenant', None)
        course = TrainingCourse.objects.get(id=course_id, tenant=tenant)
    except TrainingCourse.DoesNotExist:
        return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
    course.is_active = False
    course.save(update_fields=['is_active', 'updated_at'])
    return Response({'detail': 'Course deleted.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def training_reminders(request):
    """Return training records that are expired or expiring soon."""
    tenant = getattr(request, 'tenant', None)
    records = TrainingRecord.objects.select_related('staff', 'course').filter(staff__tenant=tenant)
    if not request.user.is_manager_or_above:
        try:
            profile = request.user.staff_profile
            records = records.filter(staff=profile)
        except StaffProfile.DoesNotExist:
            return Response([])
    # Filter to only expired or expiring soon
    from datetime import timedelta
    today = timezone.now().date()
    # Get all records with expiry dates
    records_with_expiry = records.filter(expiry_date__isnull=False)
    # Expired: expiry_date < today
    expired = list(records_with_expiry.filter(expiry_date__lt=today))
    # Expiring soon: within the next 60 days (max reminder window)
    expiring = list(records_with_expiry.filter(expiry_date__gte=today, expiry_date__lte=today + timedelta(days=60)))
    # Filter expiring to only those within their course's reminder window
    expiring_filtered = []
    for r in expiring:
        reminder_days = r.course.reminder_days_before if r.course else 30
        if r.expiry_date <= today + timedelta(days=reminder_days):
            expiring_filtered.append(r)
    all_alerts = expired + expiring_filtered
    data = TrainingRecordSerializer(all_alerts, many=True).data
    # Add alert_type field
    for item in data:
        if item.get('is_expired'):
            item['alert_type'] = 'expired'
        else:
            item['alert_type'] = 'expiring_soon'
    return Response(data)


@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def training_compliance(request):
    """Return compliance matrix: for each mandatory course, show which staff have completed it and status."""
    tenant = getattr(request, 'tenant', None)
    mandatory_courses = TrainingCourse.objects.filter(tenant=tenant, is_mandatory=True, is_active=True)
    active_staff = StaffProfile.objects.filter(tenant=tenant, is_active=True)
    today = timezone.now().date()
    matrix = []
    for course in mandatory_courses:
        staff_status = []
        for sp in active_staff:
            record = TrainingRecord.objects.filter(staff=sp, course=course).order_by('-completed_date').first()
            if not record:
                s = 'missing'
            elif record.is_expired:
                s = 'expired'
            elif record.is_expiring_soon:
                s = 'expiring_soon'
            else:
                s = 'valid'
            staff_status.append({
                'staff_id': sp.id,
                'staff_name': sp.display_name,
                'status': s,
                'expiry_date': str(record.expiry_date) if record and record.expiry_date else None,
                'completed_date': str(record.completed_date) if record and record.completed_date else None,
                'days_until_expiry': record.days_until_expiry if record else None,
            })
        matrix.append({
            'course_id': course.id,
            'course_name': course.name,
            'is_mandatory': True,
            'staff': staff_status,
        })
    return Response(matrix)


@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def absence_list(request):
    """List absence records (manager+)."""
    tenant = getattr(request, 'tenant', None)
    records = AbsenceRecord.objects.select_related('staff').filter(staff__tenant=tenant)
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
    tenant = getattr(request, 'tenant', None)
    staff = serializer.validated_data.get('staff')
    if staff and not StaffProfile.objects.filter(id=staff.id, tenant=tenant).exists():
        return Response({'error': 'Staff not found'}, status=status.HTTP_404_NOT_FOUND)
    record = serializer.save()
    return Response(AbsenceRecordSerializer(record).data, status=status.HTTP_201_CREATED)


# ── Working Hours ────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def working_hours_list(request):
    """List working hours. ?staff_id= to filter by staff."""
    tenant = getattr(request, 'tenant', None)
    qs = WorkingHours.objects.select_related('staff').filter(is_active=True, staff__tenant=tenant)
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
        tenant = getattr(request, 'tenant', None)
        wh = WorkingHours.objects.get(id=wh_id, staff__tenant=tenant)
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
        tenant = getattr(request, 'tenant', None)
        wh = WorkingHours.objects.get(id=wh_id, staff__tenant=tenant)
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
        tenant = getattr(request, 'tenant', None)
        profile = StaffProfile.objects.get(id=staff_id, tenant=tenant)
    except StaffProfile.DoesNotExist:
        return Response({'error': 'Staff not found'}, status=status.HTTP_404_NOT_FOUND)
    from datetime import datetime as _dt
    try:
        with transaction.atomic():
            WorkingHours.objects.filter(staff=profile).delete()
            created_ids = []
            for h in hours:
                # Parse time strings to datetime.time objects
                st = h['start_time']
                et = h['end_time']
                if isinstance(st, str):
                    st = _dt.strptime(st, '%H:%M').time()
                if isinstance(et, str):
                    et = _dt.strptime(et, '%H:%M').time()
                wh = WorkingHours.objects.create(
                    staff=profile,
                    day_of_week=h['day_of_week'],
                    start_time=st,
                    end_time=et,
                    break_minutes=h.get('break_minutes', 0),
                )
                created_ids.append(wh.id)
        # Re-fetch to ensure proper field types for serializer
        created = list(WorkingHours.objects.filter(id__in=created_ids).order_by('day_of_week', 'start_time'))
        return Response(WorkingHoursSerializer(created, many=True).data, status=status.HTTP_201_CREATED)
    except Exception as e:
        import traceback
        return Response({'error': str(e), 'trace': traceback.format_exc()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── Timesheets ───────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def timesheet_list(request):
    """List timesheet entries. ?staff_id=, ?date_from=, ?date_to= filters.
    Staff see own only; managers see all."""
    tenant = getattr(request, 'tenant', None)
    qs = TimesheetEntry.objects.select_related('staff').filter(staff__tenant=tenant)
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
        tenant = getattr(request, 'tenant', None)
        entry = TimesheetEntry.objects.get(id=ts_id, staff__tenant=tenant)
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

    tenant = getattr(request, 'tenant', None)
    all_wh = WorkingHours.objects.filter(is_active=True, staff__tenant=tenant, **staff_filter).select_related('staff')
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

    tenant = getattr(request, 'tenant', None)
    qs = TimesheetEntry.objects.filter(date__gte=date_from, date__lte=date_to, staff__tenant=tenant)
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


# ── Project Codes (Harvest-style) ────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def project_code_list(request):
    """List project codes. ?include_inactive=true for all."""
    tenant = getattr(request, 'tenant', None)
    qs = ProjectCode.objects.filter(tenant=tenant)
    if request.query_params.get('include_inactive') != 'true':
        qs = qs.filter(is_active=True)
    return Response(ProjectCodeSerializer(qs, many=True).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def project_code_create(request):
    """Create a project code (manager+)."""
    serializer = ProjectCodeCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    tenant = getattr(request, 'tenant', None)
    if ProjectCode.objects.filter(tenant=tenant, code=serializer.validated_data['code']).exists():
        return Response({'error': 'A project with this code already exists.'}, status=status.HTTP_400_BAD_REQUEST)
    pc = serializer.save(tenant=tenant)
    return Response(ProjectCodeSerializer(pc).data, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsManagerOrAbove])
def project_code_update(request, pc_id):
    """Update a project code (manager+)."""
    try:
        tenant = getattr(request, 'tenant', None)
        pc = ProjectCode.objects.get(id=pc_id, tenant=tenant)
    except ProjectCode.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = ProjectCodeCreateSerializer(pc, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(ProjectCodeSerializer(pc).data)


@api_view(['DELETE'])
@permission_classes([IsManagerOrAbove])
def project_code_delete(request, pc_id):
    """Deactivate a project code (manager+)."""
    try:
        tenant = getattr(request, 'tenant', None)
        pc = ProjectCode.objects.get(id=pc_id, tenant=tenant)
    except ProjectCode.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    pc.is_active = False
    pc.save(update_fields=['is_active', 'updated_at'])
    return Response({'detail': 'Project code deactivated.'})


# ── Payroll Export (CSV) ─────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def timesheet_export_csv(request):
    """Export timesheets as CSV for payroll. ?date_from=&date_to=&staff_id="""
    import csv
    from django.http import HttpResponse
    from datetime import datetime

    tenant = getattr(request, 'tenant', None)
    date_from_str = request.query_params.get('date_from')
    date_to_str = request.query_params.get('date_to')

    if not date_from_str or not date_to_str:
        return Response({'error': 'date_from and date_to are required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

    qs = TimesheetEntry.objects.filter(
        staff__tenant=tenant, date__gte=date_from, date__lte=date_to
    ).select_related('staff', 'project_code').order_by('staff__display_name', 'date')

    staff_id = request.query_params.get('staff_id')
    if staff_id:
        qs = qs.filter(staff_id=staff_id)

    response = HttpResponse(content_type='text/csv')
    filename = f'timesheets_{date_from_str}_to_{date_to_str}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        'Staff Name', 'Date', 'Day', 'Project Code', 'Project Name',
        'Scheduled Start', 'Scheduled End', 'Scheduled Hours',
        'Actual Start', 'Actual End', 'Actual Hours',
        'Variance', 'Status', 'Notes',
    ])

    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    for e in qs:
        writer.writerow([
            e.staff.display_name,
            e.date.strftime('%d/%m/%Y'),
            day_names[e.date.weekday()],
            e.project_code.code if e.project_code else '',
            e.project_code.name if e.project_code else '',
            str(e.scheduled_start or ''),
            str(e.scheduled_end or ''),
            f'{e.scheduled_hours:.2f}',
            str(e.actual_start or ''),
            str(e.actual_end or ''),
            f'{e.actual_hours:.2f}',
            f'{e.variance_hours:+.2f}',
            e.get_status_display(),
            e.notes,
        ])

    return response


# ── Payroll Summary (Monthly totals for dashboard) ───────────────────────────

@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def payroll_summary(request):
    """Monthly payroll summary for the admin dashboard.
    ?month=YYYY-MM (defaults to current month)
    Returns per-staff totals + project breakdown + grand totals.
    """
    from datetime import datetime, timedelta
    import calendar

    tenant = getattr(request, 'tenant', None)
    month_str = request.query_params.get('month')
    if month_str:
        try:
            ref = datetime.strptime(month_str + '-01', '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid month. Use YYYY-MM.'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        ref = timezone.now().date().replace(day=1)

    date_from = ref.replace(day=1)
    last_day = calendar.monthrange(ref.year, ref.month)[1]
    date_to = ref.replace(day=last_day)

    qs = TimesheetEntry.objects.filter(
        staff__tenant=tenant, date__gte=date_from, date__lte=date_to
    ).select_related('staff', 'project_code')

    # Per-staff summary
    staff_totals = {}
    project_totals = {}
    grand_scheduled = 0
    grand_actual = 0

    for e in qs:
        sid = e.staff_id
        if sid not in staff_totals:
            staff_totals[sid] = {
                'staff_id': sid,
                'staff_name': e.staff.display_name,
                'scheduled_hours': 0,
                'actual_hours': 0,
                'days_worked': 0,
                'days_absent': 0,
            }
        st = staff_totals[sid]
        st['scheduled_hours'] += e.scheduled_hours
        st['actual_hours'] += e.actual_hours
        if e.status in ('WORKED', 'LATE', 'LEFT_EARLY', 'AMENDED'):
            st['days_worked'] += 1
        elif e.status in ('ABSENT', 'SICK'):
            st['days_absent'] += 1

        grand_scheduled += e.scheduled_hours
        grand_actual += e.actual_hours

        # Project breakdown
        pc_key = e.project_code.code if e.project_code else '(No project)'
        if pc_key not in project_totals:
            project_totals[pc_key] = {
                'code': pc_key,
                'name': e.project_code.name if e.project_code else 'Unassigned',
                'is_billable': e.project_code.is_billable if e.project_code else False,
                'total_hours': 0,
            }
        project_totals[pc_key]['total_hours'] += e.actual_hours or e.scheduled_hours

    for st in staff_totals.values():
        st['scheduled_hours'] = round(st['scheduled_hours'], 2)
        st['actual_hours'] = round(st['actual_hours'], 2)
        st['variance_hours'] = round(st['actual_hours'] - st['scheduled_hours'], 2)

    for pt in project_totals.values():
        pt['total_hours'] = round(pt['total_hours'], 2)

    return Response({
        'month': date_from.strftime('%Y-%m'),
        'month_display': date_from.strftime('%B %Y'),
        'date_from': str(date_from),
        'date_to': str(date_to),
        'grand_scheduled_hours': round(grand_scheduled, 2),
        'grand_actual_hours': round(grand_actual, 2),
        'staff_count': len(staff_totals),
        'staff_summaries': sorted(staff_totals.values(), key=lambda s: s['staff_name']),
        'project_breakdown': sorted(project_totals.values(), key=lambda p: p['code']),
    })


# ═══════════════════════════════════════════════════════════
#  HOURS TALLY — contracted vs actual, credit / deficit
# ═══════════════════════════════════════════════════════════

def _week_bounds(ref_date):
    """Return (Monday, Sunday) for the week containing ref_date."""
    from datetime import timedelta
    monday = ref_date - timedelta(days=ref_date.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def _compute_tally(staff_profile, period_start, period_end):
    """Compute contracted vs actual hours for a staff member over a date range."""
    contracted_weekly = float(staff_profile.contracted_hours_per_week or 0)
    total_days = (period_end - period_start).days + 1
    contracted_total = round(contracted_weekly * total_days / 7, 2)

    entries = TimesheetEntry.objects.filter(
        staff=staff_profile,
        date__gte=period_start,
        date__lte=period_end,
    )
    actual_total = 0.0
    for e in entries:
        ah = e.actual_hours
        if ah:
            actual_total += ah

    variance = round(actual_total - contracted_total, 2)
    return {
        'contracted_hours': contracted_total,
        'actual_hours': round(actual_total, 2),
        'variance': variance,
        'status': 'credit' if variance > 0.25 else ('deficit' if variance < -0.25 else 'on_track'),
    }


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def hours_tally(request):
    """GET /api/staff-module/hours-tally/?staff_id=X&period=week|month|custom&date=YYYY-MM-DD&date_from=&date_to=
    Returns per-staff hours tally: contracted vs actual, credit/deficit.
    If no staff_id, returns tally for ALL active staff (overview).
    """
    from datetime import date, timedelta
    tenant = getattr(request, 'tenant', None)
    staff_id = request.query_params.get('staff_id')
    period = request.query_params.get('period', 'week')
    ref_str = request.query_params.get('date')

    try:
        ref = date.fromisoformat(ref_str) if ref_str else date.today()
    except ValueError:
        ref = date.today()

    if period == 'week':
        start, end = _week_bounds(ref)
    elif period == 'month':
        start = ref.replace(day=1)
        next_m = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        end = next_m - timedelta(days=1)
    elif period == 'custom':
        try:
            start = date.fromisoformat(request.query_params.get('date_from', ''))
            end = date.fromisoformat(request.query_params.get('date_to', ''))
        except ValueError:
            start, end = _week_bounds(ref)
    else:
        start, end = _week_bounds(ref)

    if staff_id:
        try:
            s = StaffProfile.objects.get(id=staff_id, tenant=tenant)
        except StaffProfile.DoesNotExist:
            return Response({'error': 'Staff not found'}, status=status.HTTP_404_NOT_FOUND)
        tally = _compute_tally(s, start, end)
        tally['staff_id'] = s.id
        tally['staff_name'] = s.display_name
        tally['pay_type'] = s.pay_type
        tally['overtime_eligible'] = s.overtime_eligible
        tally['contracted_hours_per_week'] = float(s.contracted_hours_per_week or 0)
        return Response({
            'period': period, 'start': start.isoformat(), 'end': end.isoformat(),
            'tally': [tally],
        })
    else:
        staff_qs = StaffProfile.objects.filter(tenant=tenant, is_active=True)
        tallies = []
        for s in staff_qs:
            t = _compute_tally(s, start, end)
            t['staff_id'] = s.id
            t['staff_name'] = s.display_name
            t['pay_type'] = s.pay_type
            t['overtime_eligible'] = s.overtime_eligible
            t['contracted_hours_per_week'] = float(s.contracted_hours_per_week or 0)
            tallies.append(t)
        return Response({
            'period': period, 'start': start.isoformat(), 'end': end.isoformat(),
            'tally': tallies,
        })


# ═══════════════════════════════════════════════════════════
#  LEAVE BALANCE — allowance, taken, remaining per staff
# ═══════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def leave_balance(request):
    """GET /api/staff-module/leave-balance/?staff_id=X&year=2026
    Returns leave allowance, taken, remaining for each staff member.
    Counts APPROVED leave requests where leave_type=ANNUAL for the given year.
    """
    from datetime import date, timedelta
    tenant = getattr(request, 'tenant', None)
    staff_id = request.query_params.get('staff_id')
    year = int(request.query_params.get('year', date.today().year))

    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)

    if staff_id:
        staff_qs = StaffProfile.objects.filter(id=staff_id, tenant=tenant)
    else:
        staff_qs = StaffProfile.objects.filter(tenant=tenant, is_active=True)

    result = []
    for s in staff_qs:
        allowance = float(s.annual_leave_days or 28)
        approved = LeaveRequest.objects.filter(
            staff=s,
            leave_type='ANNUAL',
            status='APPROVED',
            start_date__lte=year_end,
            end_date__gte=year_start,
        )
        taken_days = 0.0
        for lr in approved:
            lr_start = max(lr.start_date, year_start)
            lr_end = min(lr.end_date, year_end)
            d = lr_start
            while d <= lr_end:
                if d.weekday() < 5:
                    taken_days += 1
                d += timedelta(days=1)

        remaining = round(allowance - taken_days, 1)
        result.append({
            'staff_id': s.id,
            'staff_name': s.display_name,
            'year': year,
            'allowance': allowance,
            'taken': taken_days,
            'remaining': remaining,
            'pay_type': s.pay_type,
        })

    return Response({'year': year, 'balances': result})


# ═══════════════════════════════════════════════════════════
#  QUICK TIME LOG — easy actual hours entry per day
# ═══════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def quick_time_log(request):
    """POST /api/staff-module/timesheets/quick-log/
    Body: { staff_id, date, actual_start (HH:MM), actual_end (HH:MM), actual_break_minutes?, notes? }
    Creates or updates a timesheet entry for the given staff+date.
    """
    from datetime import date, datetime
    d = request.data
    staff_id = d.get('staff_id')
    log_date_str = d.get('date')
    actual_start_str = d.get('actual_start')
    actual_end_str = d.get('actual_end')
    break_mins = int(d.get('actual_break_minutes', 0))
    notes = d.get('notes', '')

    if not staff_id or not log_date_str or not actual_start_str or not actual_end_str:
        return Response({'error': 'staff_id, date, actual_start, actual_end are required'}, status=status.HTTP_400_BAD_REQUEST)

    tenant = getattr(request, 'tenant', None)
    try:
        staff_member = StaffProfile.objects.get(id=staff_id, tenant=tenant)
    except StaffProfile.DoesNotExist:
        return Response({'error': 'Staff not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        log_date = date.fromisoformat(log_date_str)
    except ValueError:
        return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)

    actual_start = datetime.strptime(actual_start_str, '%H:%M').time()
    actual_end = datetime.strptime(actual_end_str, '%H:%M').time()

    entry, created = TimesheetEntry.objects.get_or_create(
        staff=staff_member,
        date=log_date,
        defaults={
            'actual_start': actual_start,
            'actual_end': actual_end,
            'actual_break_minutes': break_mins,
            'notes': notes,
            'status': 'WORKED',
        }
    )

    if not created:
        entry.actual_start = actual_start
        entry.actual_end = actual_end
        entry.actual_break_minutes = break_mins
        if notes:
            entry.notes = notes
        if entry.status == 'SCHEDULED':
            entry.status = 'WORKED'
        entry.save()

    serializer = TimesheetEntrySerializer(entry)
    return Response({
        'entry': serializer.data,
        'created': created,
        'message': f'Hours logged for {staff_member.display_name} on {log_date}',
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
