from rest_framework import serializers
from django.utils import timezone
from .models import Service, TimeSlot, Booking


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            'id', 'name', 'description', 'category', 'duration_minutes',
            'price_pence', 'deposit_pence', 'colour', 'is_active', 'sort_order',
        ]
        read_only_fields = fields


class ServiceWriteSerializer(serializers.ModelSerializer):
    """Writable serializer for admin service management."""
    class Meta:
        model = Service
        fields = [
            'name', 'description', 'category', 'duration_minutes',
            'price_pence', 'deposit_pence', 'colour', 'is_active', 'sort_order',
        ]


class TimeSlotSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True, default=None)
    current_booking_count = serializers.IntegerField(read_only=True)
    has_capacity = serializers.BooleanField(read_only=True)

    class Meta:
        model = TimeSlot
        fields = [
            'id', 'date', 'start_time', 'end_time',
            'service', 'service_name', 'max_bookings',
            'current_booking_count', 'has_capacity', 'is_available',
        ]
        read_only_fields = fields


class BookingCreateSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=255)
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(max_length=50, required=False, default='')
    service_id = serializers.IntegerField()
    time_slot_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, default='')

    def validate_service_id(self, value):
        try:
            Service.objects.get(id=value, is_active=True)
        except Service.DoesNotExist:
            raise serializers.ValidationError('Service not found or inactive.')
        return value

    def validate_time_slot_id(self, value):
        try:
            slot = TimeSlot.objects.get(id=value, is_available=True)
        except TimeSlot.DoesNotExist:
            raise serializers.ValidationError('Time slot not found or unavailable.')
        if slot.date < timezone.now().date():
            raise serializers.ValidationError('Cannot book a slot in the past.')
        if not slot.has_capacity:
            raise serializers.ValidationError('This time slot is fully booked.')
        return value

    def validate(self, data):
        try:
            slot = TimeSlot.objects.get(id=data['time_slot_id'])
            if slot.service_id and slot.service_id != data['service_id']:
                raise serializers.ValidationError(
                    {'time_slot_id': 'This slot is reserved for a different service.'}
                )
        except TimeSlot.DoesNotExist:
            pass
        return data


class BookingSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True, default=None)
    service_duration = serializers.IntegerField(source='service.duration_minutes', read_only=True, default=None)
    slot_date = serializers.DateField(source='time_slot.date', read_only=True, default=None)
    slot_start = serializers.TimeField(source='time_slot.start_time', read_only=True, default=None)
    slot_end = serializers.TimeField(source='time_slot.end_time', read_only=True, default=None)

    class Meta:
        model = Booking
        fields = [
            'id', 'customer_name', 'customer_email', 'customer_phone',
            'service', 'service_name', 'service_duration',
            'time_slot', 'slot_date', 'slot_start', 'slot_end',
            'price_pence', 'deposit_pence',
            'status', 'notes', 'cancellation_reason',
            'payment_session_id',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields


class BookingCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, default='')
