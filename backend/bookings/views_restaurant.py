"""
Restaurant-specific API views — Table CRUD, ServiceWindow CRUD, and availability endpoint.
"""
from datetime import datetime, timedelta, time as dt_time
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum

from .models_restaurant import Table, ServiceWindow
from .models import Booking
from .serializers_restaurant import TableSerializer, ServiceWindowSerializer


class TableViewSet(viewsets.ModelViewSet):
    serializer_class = TableSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            return Table.objects.none()
        return Table.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        serializer.save(tenant=tenant)


class ServiceWindowViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceWindowSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            return ServiceWindow.objects.none()
        return ServiceWindow.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        serializer.save(tenant=tenant)


@api_view(['GET'])
@permission_classes([AllowAny])
def restaurant_availability(request):
    """
    GET /api/bookings/restaurant-availability/?date=YYYY-MM-DD&party_size=N

    Returns available time slots for a restaurant on a given date and party size.
    Checks table inventory against existing bookings within each service window.
    """
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=400)

    date_str = request.query_params.get('date')
    party_size_str = request.query_params.get('party_size', '2')

    if not date_str:
        return Response({'error': 'date parameter required'}, status=400)

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Invalid date format, use YYYY-MM-DD'}, status=400)

    try:
        party_size = int(party_size_str)
    except ValueError:
        return Response({'error': 'party_size must be an integer'}, status=400)

    if party_size < 1:
        return Response({'error': 'party_size must be >= 1'}, status=400)

    # day_of_week: Python weekday() returns 0=Monday which matches our WEEKDAY_CHOICES
    day_of_week = target_date.weekday()

    # Get active service windows for this day
    windows = ServiceWindow.objects.filter(
        tenant=tenant, day_of_week=day_of_week, active=True
    )

    if not windows.exists():
        return Response({'windows': [], 'message': 'Restaurant is closed on this day'})

    # Get active tables that can seat this party
    suitable_tables = Table.objects.filter(
        tenant=tenant, active=True, max_seats__gte=party_size
    )

    if not suitable_tables.exists():
        return Response({'windows': [], 'message': 'No tables available for this party size'})

    # Get existing bookings for this date (use start_time__date since Booking has no date field)
    existing_bookings = Booking.objects.filter(
        tenant=tenant,
        start_time__date=target_date,
        status__in=['confirmed', 'pending'],
    )

    total_tables = suitable_tables.count()
    result_windows = []

    for window in windows:
        slots = []
        turn_minutes = window.turn_time_minutes

        # Generate time slots at 15-minute intervals from open_time to last_booking_time
        current_time = window.open_time
        last_time = window.last_booking_time

        while current_time <= last_time:
            # Calculate end time for this slot
            slot_start_dt = datetime.combine(target_date, current_time)
            slot_end_dt = slot_start_dt + timedelta(minutes=turn_minutes)
            slot_end_time = slot_end_dt.time()

            # Count overlapping bookings: a booking overlaps if it starts before slot ends
            # and ends after slot starts
            overlapping_bookings = existing_bookings.filter(
                start_time__date=target_date,
                start_time__time__lt=slot_end_time,
                end_time__time__gt=current_time,
            )

            # Count booked tables (each booking uses one table)
            booked_count = overlapping_bookings.count()
            available_tables = max(0, total_tables - booked_count)

            # Check total covers in this window
            total_covers_booked = overlapping_bookings.aggregate(
                total=Sum('party_size')
            )['total'] or 0
            covers_remaining = window.max_covers - total_covers_booked

            has_capacity = available_tables > 0 and covers_remaining >= party_size

            slots.append({
                'start_time': current_time.strftime('%H:%M'),
                'end_time': slot_end_time.strftime('%H:%M'),
                'has_capacity': has_capacity,
                'tables_available': available_tables,
                'covers_remaining': covers_remaining,
            })

            # Advance by 15 minutes
            current_time = (slot_start_dt + timedelta(minutes=15)).time()

        result_windows.append({
            'id': window.id,
            'name': window.name,
            'open_time': window.open_time.strftime('%H:%M'),
            'close_time': window.close_time.strftime('%H:%M'),
            'slots': slots,
        })

    return Response({'windows': result_windows})


@api_view(['GET'])
@permission_classes([AllowAny])
def restaurant_available_dates(request):
    """
    GET /api/bookings/restaurant-available-dates/?party_size=N&weeks=4

    Returns a list of dates in the next N weeks that have at least one available slot.
    """
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=400)

    party_size_str = request.query_params.get('party_size', '2')
    weeks_str = request.query_params.get('weeks', '4')

    try:
        party_size = int(party_size_str)
        weeks = int(weeks_str)
    except ValueError:
        return Response({'error': 'Invalid parameters'}, status=400)

    # Get all active service window days
    active_days = set(
        ServiceWindow.objects.filter(tenant=tenant, active=True)
        .values_list('day_of_week', flat=True)
    )

    # Get suitable tables
    has_tables = Table.objects.filter(
        tenant=tenant, active=True, max_seats__gte=party_size
    ).exists()

    if not has_tables or not active_days:
        return Response({'dates': []})

    # Generate dates for the next N weeks
    today = datetime.now().date()
    available_dates = []
    for i in range(weeks * 7):
        d = today + timedelta(days=i)
        if d.weekday() in active_days:
            available_dates.append(d.strftime('%Y-%m-%d'))

    return Response({'dates': available_dates})
