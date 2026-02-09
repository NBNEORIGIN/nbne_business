from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import transaction
from accounts.models import User
from accounts.permissions import IsStaffOrAbove, IsManagerOrAbove, IsOwner
from .models import StaffProfile, Shift, LeaveRequest, TrainingRecord, AbsenceRecord
from .serializers import (
    StaffProfileSerializer, ShiftSerializer, ShiftCreateSerializer,
    LeaveRequestSerializer, LeaveCreateSerializer, LeaveReviewSerializer,
    TrainingRecordSerializer, TrainingCreateSerializer,
    AbsenceRecordSerializer, AbsenceCreateSerializer,
)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def staff_list(request):
    """List all staff profiles (staff+)."""
    profiles = StaffProfile.objects.select_related('user').all()
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
    password = request.data.get('password', 'changeme123')

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
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name,
            role=role, is_staff=(role in ('manager', 'owner')),
        )
        profile = StaffProfile.objects.create(
            user=user,
            display_name=f'{first_name} {last_name}',
            phone=phone,
            hire_date=timezone.now().date(),
        )
    return Response(StaffProfileSerializer(profile).data, status=status.HTTP_201_CREATED)


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
