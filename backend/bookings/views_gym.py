"""
Gym/Fitness-specific API views — ClassType CRUD, ClassSession CRUD, and timetable endpoint.
"""
from datetime import datetime, timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q

from .models_gym import ClassType, ClassSession
from .models import Booking
from .serializers_gym import ClassTypeSerializer, ClassSessionSerializer


class ClassTypeViewSet(viewsets.ModelViewSet):
    serializer_class = ClassTypeSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            return ClassType.objects.none()
        return ClassType.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        serializer.save(tenant=tenant)


class ClassSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ClassSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            return ClassSession.objects.none()
        qs = ClassSession.objects.filter(tenant=tenant).select_related('class_type', 'instructor')
        day = self.request.query_params.get('day')
        if day is not None:
            qs = qs.filter(day_of_week=int(day))
        return qs

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        serializer.save(tenant=tenant)


@api_view(['GET'])
@permission_classes([AllowAny])
def gym_timetable(request):
    """
    GET /api/bookings/gym-timetable/?date=YYYY-MM-DD

    Returns the weekly timetable for a gym tenant, with booking counts per session.
    If date is provided, returns the timetable for that week (Mon-Sun).
    """
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=400)

    date_str = request.query_params.get('date')
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format, use YYYY-MM-DD'}, status=400)
    else:
        target_date = datetime.now().date()

    # Calculate week boundaries (Monday to Sunday)
    monday = target_date - timedelta(days=target_date.weekday())
    sunday = monday + timedelta(days=6)

    # Get all active sessions
    sessions = ClassSession.objects.filter(
        tenant=tenant, active=True
    ).select_related('class_type', 'instructor')

    # Get bookings for this week to compute spots remaining
    week_bookings = Booking.objects.filter(
        tenant=tenant,
        start_time__date__gte=monday,
        start_time__date__lte=sunday,
        status__in=['confirmed', 'pending'],
    )

    result = []
    for session in sessions:
        # Calculate the actual date for this session in the target week
        session_date = monday + timedelta(days=session.day_of_week)

        # Count bookings for this specific session on this date
        # Match by class_type service name and time
        booked_count = week_bookings.filter(
            start_time__date=session_date,
            start_time__time=session.start_time,
            service__name=session.class_type.name,
        ).count()

        capacity = session.capacity
        spots_remaining = max(0, capacity - booked_count)

        result.append({
            'id': session.id,
            'class_type': {
                'id': session.class_type.id,
                'name': session.class_type.name,
                'description': session.class_type.description,
                'category': session.class_type.category,
                'duration_minutes': session.class_type.duration_minutes,
                'difficulty': session.class_type.difficulty,
                'colour': session.class_type.colour,
                'price_pence': session.class_type.price_pence,
            },
            'instructor': {
                'id': session.instructor.id,
                'name': session.instructor.name,
            } if session.instructor else None,
            'day_of_week': session.day_of_week,
            'day_of_week_display': session.get_day_of_week_display(),
            'date': session_date.strftime('%Y-%m-%d'),
            'start_time': session.start_time.strftime('%H:%M'),
            'end_time': session.end_time.strftime('%H:%M'),
            'room': session.room,
            'capacity': capacity,
            'booked': booked_count,
            'spots_remaining': spots_remaining,
            'is_full': spots_remaining == 0,
        })

    return Response({
        'week_start': monday.strftime('%Y-%m-%d'),
        'week_end': sunday.strftime('%Y-%m-%d'),
        'sessions': result,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def gym_class_types(request):
    """
    GET /api/bookings/gym-class-types/

    Public endpoint returning active class types for the gym.
    """
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=400)

    class_types = ClassType.objects.filter(tenant=tenant, active=True)
    data = ClassTypeSerializer(class_types, many=True).data
    return Response(data)
