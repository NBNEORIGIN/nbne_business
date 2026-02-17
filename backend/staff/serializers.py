from rest_framework import serializers
from .models import StaffProfile, Shift, LeaveRequest, TrainingCourse, TrainingRecord, AbsenceRecord, WorkingHours, TimesheetEntry, ProjectCode


class StaffProfileSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='user.role', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = StaffProfile
        fields = [
            'id', 'display_name', 'role', 'email', 'phone',
            'emergency_contact_name', 'emergency_contact_phone',
            'hire_date', 'is_active', 'notes',
            'pay_type', 'overtime_eligible', 'contracted_hours_per_week',
            'hourly_rate', 'annual_leave_days',
            'created_at',
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


class TrainingCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingCourse
        fields = [
            'id', 'name', 'provider', 'is_mandatory', 'renewal_months',
            'reminder_days_before', 'description', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class TrainingCourseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingCourse
        fields = ['name', 'provider', 'is_mandatory', 'renewal_months', 'reminder_days_before', 'description']


class TrainingRecordSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.display_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True, default=None)
    is_mandatory = serializers.BooleanField(source='course.is_mandatory', read_only=True, default=False)
    is_expired = serializers.BooleanField(read_only=True)
    is_expiring_soon = serializers.BooleanField(read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)

    class Meta:
        model = TrainingRecord
        fields = [
            'id', 'staff', 'staff_name', 'course', 'course_name', 'is_mandatory',
            'title', 'provider', 'completed_date', 'expiry_date',
            'is_expired', 'is_expiring_soon', 'days_until_expiry',
            'certificate_reference', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'is_expired', 'is_expiring_soon', 'days_until_expiry']


class TrainingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingRecord
        fields = ['staff', 'course', 'title', 'provider', 'completed_date', 'expiry_date', 'certificate_reference', 'notes']


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


class ProjectCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCode
        fields = [
            'id', 'code', 'name', 'client_name', 'is_billable',
            'hourly_rate', 'is_active', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ProjectCodeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCode
        fields = ['code', 'name', 'client_name', 'is_billable', 'hourly_rate', 'notes']


class TimesheetEntrySerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.display_name', read_only=True)
    scheduled_hours = serializers.FloatField(read_only=True)
    actual_hours = serializers.FloatField(read_only=True)
    variance_hours = serializers.FloatField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    project_code_display = serializers.CharField(source='project_code.code', read_only=True, default=None)
    project_name = serializers.CharField(source='project_code.name', read_only=True, default=None)

    class Meta:
        model = TimesheetEntry
        fields = [
            'id', 'staff', 'staff_name', 'date',
            'project_code', 'project_code_display', 'project_name',
            'scheduled_start', 'scheduled_end', 'scheduled_break_minutes', 'scheduled_hours',
            'actual_start', 'actual_end', 'actual_break_minutes', 'actual_hours',
            'variance_hours', 'status', 'status_display', 'notes',
            'approved_by', 'approved_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'scheduled_hours', 'actual_hours', 'variance_hours']


class TimesheetUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimesheetEntry
        fields = ['actual_start', 'actual_end', 'actual_break_minutes', 'status', 'notes', 'project_code']
