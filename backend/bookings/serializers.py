from rest_framework import serializers
from .models import Service, Staff, Client, Booking, Session


class ServiceSerializer(serializers.ModelSerializer):
    price_pence = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(source='active', required=False)
    staff_ids = serializers.SerializerMethodField()
    risk_indicator = serializers.CharField(read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)

    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'category', 'duration_minutes', 'price',
                  'price_pence', 'payment_type', 'deposit_pence', 'deposit_percentage',
                  'colour', 'sort_order', 'active', 'is_active', 'staff_ids',
                  'demand_index', 'peak_time_multiplier', 'off_peak_discount_allowed',
                  'avg_booking_value', 'total_revenue', 'total_bookings',
                  'no_show_rate', 'avg_risk_score', 'peak_utilisation_rate',
                  'off_peak_utilisation_rate', 'recommended_base_price',
                  'recommended_deposit_percent', 'recommended_payment_type',
                  'price_elasticity_index', 'recommendation_reason',
                  'recommendation_confidence', 'last_optimised_at',
                  'auto_optimise_enabled', 'deposit_strategy',
                  'smart_pricing_enabled', 'off_peak_discount_percent',
                  'risk_indicator',
                  'created_at', 'updated_at']
        read_only_fields = ['avg_booking_value', 'total_revenue', 'total_bookings',
                           'no_show_rate', 'avg_risk_score', 'peak_utilisation_rate',
                           'off_peak_utilisation_rate', 'recommended_base_price',
                           'recommended_deposit_percent', 'recommended_payment_type',
                           'price_elasticity_index', 'recommendation_reason',
                           'recommendation_confidence', 'last_optimised_at',
                           'risk_indicator']

    def get_staff_ids(self, obj):
        return list(obj.staff_members.values_list('id', flat=True))


class StaffSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    services = ServiceSerializer(many=True, read_only=True)
    service_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Service.objects.all(), 
        source='services', 
        write_only=True,
        required=False
    )

    class Meta:
        model = Staff
        fields = ['id', 'name', 'role', 'email', 'phone', 'photo_url', 'services', 'service_ids', 'break_start', 'break_end', 'active', 'created_at', 'updated_at']


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'name', 'email', 'phone', 'notes', 'created_at', 'updated_at']


class BookingSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    client_email = serializers.CharField(source='client.email', read_only=True)
    client_phone = serializers.CharField(source='client.phone', read_only=True)
    client_notes = serializers.CharField(source='client.notes', read_only=True)
    client_reliability_score = serializers.FloatField(source='client.reliability_score', read_only=True)
    client_lifetime_value = serializers.DecimalField(source='client.lifetime_value', max_digits=10, decimal_places=2, read_only=True)
    client_total_bookings = serializers.IntegerField(source='client.total_bookings', read_only=True)
    client_completed_bookings = serializers.IntegerField(source='client.completed_bookings', read_only=True)
    client_cancelled_bookings = serializers.IntegerField(source='client.cancelled_bookings', read_only=True)
    client_no_show_count = serializers.IntegerField(source='client.no_show_count', read_only=True)
    client_consecutive_no_shows = serializers.IntegerField(source='client.consecutive_no_shows', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_price = serializers.DecimalField(source='service.price', max_digits=10, decimal_places=2, read_only=True)
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    
    class Meta:
        model = Booking
        fields = ['id', 'client', 'client_name', 'client_email', 'client_phone', 'client_notes',
                  'client_reliability_score', 'client_lifetime_value', 'client_total_bookings',
                  'client_completed_bookings', 'client_cancelled_bookings',
                  'client_no_show_count', 'client_consecutive_no_shows',
                  'service', 'service_name', 'service_price', 'staff', 'staff_name', 
                  'start_time', 'end_time', 'status', 'notes',
                  'payment_status', 'payment_amount', 'payment_type',
                  'risk_score', 'risk_level', 'revenue_at_risk',
                  'recommended_payment_type', 'recommended_deposit_percent',
                  'recommended_price_adjustment', 'recommended_incentive',
                  'recommendation_reason', 'override_applied',
                  'created_at', 'updated_at']
        read_only_fields = ['end_time', 'created_at', 'updated_at',
                           'risk_score', 'risk_level', 'revenue_at_risk',
                           'recommended_payment_type', 'recommended_deposit_percent',
                           'recommended_price_adjustment', 'recommended_incentive',
                           'recommendation_reason', 'override_applied',
                           'client_name', 'client_email', 'client_phone', 'client_notes',
                           'client_reliability_score', 'client_lifetime_value',
                           'client_total_bookings', 'client_completed_bookings',
                           'client_cancelled_bookings', 'client_no_show_count',
                           'client_consecutive_no_shows', 'service_price']


class SessionSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    enrollment_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    available_spots = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Session
        fields = ['id', 'title', 'description', 'service', 'service_name', 'staff', 'staff_name',
                  'start_time', 'end_time', 'capacity', 'enrollment_count', 'is_full', 'available_spots',
                  'active', 'created_at', 'updated_at']
