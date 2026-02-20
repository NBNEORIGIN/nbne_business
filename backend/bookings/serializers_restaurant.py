from rest_framework import serializers
from .models_restaurant import Table, ServiceWindow


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = [
            'id', 'name', 'min_seats', 'max_seats',
            'combinable', 'combine_with', 'zone',
            'active', 'sort_order', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ServiceWindowSerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = ServiceWindow
        fields = [
            'id', 'name', 'day_of_week', 'day_of_week_display',
            'open_time', 'close_time', 'last_booking_time',
            'turn_time_minutes', 'max_covers',
            'active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
