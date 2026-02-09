from rest_framework import serializers
from .models import StaffProfile, Shift, LeaveRequest, TrainingRecord, AbsenceRecord, WorkingHours, TimesheetEntry


class StaffProfileSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='user.role', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = StaffProfile
        fields = [
            'id', 'display_name', 'role', 'email', 'phone',
            'emergency_contact_name', 'emergency_contact_phone',
            'hire_date', 'is_active', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ShiftSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.display_name', read_only=True)
    duration_hours = serializers.FloatField(read_only=True)

    class Meta:
        model = Shift
        fields = [
            'id', 'staff', 'staff_name', 'date', 'start_time', 'end_time',
            'duration_hours', 'location', 'notes', 'is_published', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'duration_hours']


class ShiftCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ['staff', 'date', 'start_time', 'end_time', 'location', 'notes', 'is_published']


class LeaveRequestSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.display_name', read_only=True)
    duration_days = serializers.IntegerField(read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.display_name', read_only=True, default=None)

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'staff', 'staff_name', 'leave_type', 'start_date', 'end_date',
            'duration_days', 'reason', 'status', 'reviewed_by_name', 'reviewed_at', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'duration_days', 'reviewed_by_name', 'reviewed_at']


class LeaveCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = ['staff', 'leave_type', 'start_date', 'end_date', 'reason']


class LeaveReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['APPROVED', 'REJECTED'])


class TrainingRecordSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.display_name', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = TrainingRecord
        fields = [
            'id', 'staff', 'staff_name', 'title', 'provider',
            'completed_date', 'expiry_date', 'is_expired',
            'certificate_reference', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'is_expired']


class TrainingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingRecord
        fields = ['staff', 'title', 'provider', 'completed_date', 'expiry_date', 'certificate_reference', 'notes']


class AbsenceRecordSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.display_name', read_only=True)

    class Meta:
        model = AbsenceRecord
        fields = [
            'id', 'staff', 'staff_name', 'record_type', 'date',
            'duration_minutes', 'reason', 'is_authorised', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class AbsenceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbsenceRecord
        fields = ['staff', 'record_type', 'date', 'duration_minutes', 'reason', 'is_authorised']


class WorkingHoursSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.display_name', read_only=True)
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    scheduled_hours = serializers.FloatField(read_only=True)

    class Meta:
        model = WorkingHours
        fields = [
            'id', 'staff', 'staff_name', 'day_of_week', 'day_name',
            'start_time', 'end_time', 'break_minutes', 'scheduled_hours', 'is_active',
        ]
        read_only_fields = ['id']


class WorkingHoursCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkingHours
        fields = ['staff', 'day_of_week', 'start_time', 'end_time', 'break_minutes', 'is_active']


class TimesheetEntrySerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.display_name', read_only=True)
    scheduled_hours = serializers.FloatField(read_only=True)
    actual_hours = serializers.FloatField(read_only=True)
    variance_hours = serializers.FloatField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = TimesheetEntry
        fields = [
            'id', 'staff', 'staff_name', 'date',
            'scheduled_start', 'scheduled_end', 'scheduled_break_minutes', 'scheduled_hours',
            'actual_start', 'actual_end', 'actual_break_minutes', 'actual_hours',
            'variance_hours', 'status', 'status_display', 'notes',
            'approved_by', 'approved_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'scheduled_hours', 'actual_hours', 'variance_hours']


class TimesheetUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimesheetEntry
        fields = ['actual_start', 'actual_end', 'actual_break_minutes', 'status', 'notes']
