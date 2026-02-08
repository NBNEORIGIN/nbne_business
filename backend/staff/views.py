from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from accounts.permissions import IsStaffOrAbove, IsManagerOrAbove
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
