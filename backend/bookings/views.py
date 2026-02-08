import uuid
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.db import transaction as db_transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from datetime import timedelta
from accounts.permissions import IsManagerOrAbove, IsStaffOrAbove
from .models import Service, TimeSlot, Booking
from .serializers import (
    ServiceSerializer, ServiceWriteSerializer, TimeSlotSerializer,
    BookingCreateSerializer, BookingSerializer, BookingCancelSerializer,
)


def _payments_available():
    return (
        getattr(settings, 'PAYMENTS_MODULE_ENABLED', False)
        and getattr(settings, 'PAYMENTS_ENABLED', False)
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def service_list(request):
    """List all active services (public)."""
    services = Service.objects.filter(is_active=True)
    serializer = ServiceSerializer(services, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def service_detail(request, service_id):
    """Get a single service by ID (public)."""
    try:
        service = Service.objects.get(id=service_id, is_active=True)
    except Service.DoesNotExist:
        return Response({'error': 'Service not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(ServiceSerializer(service).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def service_create(request):
    """Create a new service (manager/owner)."""
    serializer = ServiceWriteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    service = serializer.save()
    return Response(ServiceSerializer(service).data, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsManagerOrAbove])
def service_update(request, service_id):
    """Update a service (manager/owner)."""
    try:
        service = Service.objects.get(id=service_id)
    except Service.DoesNotExist:
        return Response({'error': 'Service not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = ServiceWriteSerializer(service, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(ServiceSerializer(service).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def available_slots(request):
    """List available time slots (public)."""
    service_id = request.query_params.get('service_id')
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')

    today = timezone.now().date()
    if date_from:
        try:
            from datetime import date as dt_date
            date_from = dt_date.fromisoformat(date_from)
        except ValueError:
            return Response({'error': 'Invalid date_from format.'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        date_from = today

    if date_to:
        try:
            from datetime import date as dt_date
            date_to = dt_date.fromisoformat(date_to)
        except ValueError:
            return Response({'error': 'Invalid date_to format.'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        date_to = date_from + timedelta(days=14)

    if date_from < today:
        date_from = today

    slots = TimeSlot.objects.filter(
        date__gte=date_from, date__lte=date_to, is_available=True,
    ).select_related('service')

    if service_id:
        slots = slots.filter(Q(service_id=service_id) | Q(service__isnull=True))

    result = [s for s in slots if s.has_capacity]
    return Response(TimeSlotSerializer(result, many=True).data)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_booking(request):
    """Create a new booking (public). Deposit computed server-side."""
    serializer = BookingCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    checkout_url = None

    with db_transaction.atomic():
        service = Service.objects.get(id=data['service_id'])
        time_slot = TimeSlot.objects.select_for_update().get(id=data['time_slot_id'])

        active_count = Booking.objects.filter(
            time_slot=time_slot
        ).exclude(status='CANCELLED').count()

        if active_count >= time_slot.max_bookings:
            return Response(
                {'error': 'This time slot is no longer available.'},
                status=status.HTTP_409_CONFLICT
            )

        deposit_pence = service.deposit_pence
        needs_payment = deposit_pence > 0 and _payments_available()

        booking = Booking(
            customer_name=data['customer_name'],
            customer_email=data['customer_email'],
            customer_phone=data.get('customer_phone', ''),
            service=service,
            time_slot=time_slot,
            price_pence=service.price_pence,
            deposit_pence=deposit_pence,
            status='PENDING_PAYMENT' if needs_payment else 'PENDING',
            notes=data.get('notes', ''),
        )
        booking.save()

        if needs_payment:
            try:
                from payments.views import create_checkout_session_internal
                base_url = f"{request.scheme}://{request.get_host()}"
                payment_data = {
                    'payable_type': 'booking',
                    'payable_id': str(booking.id),
                    'amount_pence': deposit_pence,
                    'currency': getattr(settings, 'DEFAULT_CURRENCY', 'GBP'),
                    'customer': {
                        'email': data['customer_email'],
                        'name': data['customer_name'],
                        'phone': data.get('customer_phone', ''),
                    },
                    'success_url': f"{base_url}/?booking_id={booking.id}&status=success",
                    'cancel_url': f"{base_url}/?booking_id={booking.id}&status=cancel",
                    'metadata': {
                        'service_name': service.name,
                        'slot_date': str(time_slot.date),
                        'slot_time': str(time_slot.start_time),
                    },
                    'idempotency_key': f"booking-{booking.id}-{uuid.uuid4()}",
                }
                payment_result = create_checkout_session_internal(payment_data)
                checkout_url = payment_result.get('checkout_url')
                booking.payment_session_id = payment_result.get('payment_session_id', '')
                booking.save(update_fields=['payment_session_id'])
            except Exception as e:
                booking.status = 'CANCELLED'
                booking.notes += f"\n[Payment error: {str(e)}]"
                booking.save(update_fields=['status', 'notes', 'updated_at'])
                return Response(
                    {'error': f'Payment setup failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    response_data = BookingSerializer(booking).data
    if checkout_url:
        response_data['checkout_url'] = checkout_url
    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def booking_list(request):
    """List all bookings (staff+). Supports ?status= and ?email= filters."""
    bookings = Booking.objects.select_related('service', 'time_slot').all()
    status_filter = request.query_params.get('status')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    email = request.query_params.get('email')
    if email:
        bookings = bookings.filter(customer_email__icontains=email)
    limit = int(request.query_params.get('limit', 100))
    return Response(BookingSerializer(bookings[:limit], many=True).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def booking_detail(request, booking_id):
    """Get booking details by ID."""
    try:
        booking = Booking.objects.select_related('service', 'time_slot').get(id=booking_id)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(BookingSerializer(booking).data)


@api_view(['POST'])
@permission_classes([AllowAny])
def cancel_booking(request, booking_id):
    """Cancel a booking."""
    try:
        booking = Booking.objects.select_related('time_slot').get(id=booking_id)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    if booking.status == 'CANCELLED':
        return Response({'error': 'Already cancelled.'}, status=status.HTTP_400_BAD_REQUEST)
    cancel_ser = BookingCancelSerializer(data=request.data)
    cancel_ser.is_valid(raise_exception=True)
    booking.cancel(reason=cancel_ser.validated_data.get('reason', ''))
    return Response(BookingSerializer(booking).data)


@api_view(['POST'])
@permission_classes([IsStaffOrAbove])
def confirm_booking(request, booking_id):
    """Confirm a pending booking (staff+)."""
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    if booking.status not in ('PENDING', 'PENDING_PAYMENT'):
        return Response({'error': f'Cannot confirm booking with status {booking.status}.'}, status=status.HTTP_400_BAD_REQUEST)
    booking.confirm()
    return Response(BookingSerializer(booking).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def booking_lookup(request):
    """Look up bookings by customer email (public)."""
    email = request.query_params.get('email', '').strip()
    if not email:
        return Response({'error': 'email parameter required.'}, status=status.HTTP_400_BAD_REQUEST)
    bookings = Booking.objects.filter(
        customer_email__iexact=email
    ).select_related('service', 'time_slot').order_by('-created_at')[:20]
    return Response(BookingSerializer(bookings, many=True).data)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def payment_webhook_callback(request):
    """Callback from payments module."""
    payable_type = request.data.get('payable_type')
    payable_id = request.data.get('payable_id')
    payment_status = request.data.get('status')

    if payable_type != 'booking':
        return Response({'message': 'Not a booking payment, ignored.'})
    try:
        booking = Booking.objects.get(id=payable_id)
    except (Booking.DoesNotExist, ValueError):
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

    if payment_status == 'succeeded' and booking.status == 'PENDING_PAYMENT':
        booking.confirm()
    elif payment_status in ('failed', 'canceled') and booking.status in ('PENDING_PAYMENT', 'PENDING'):
        booking.cancel(reason=f'Payment {payment_status}')

    return Response({'booking_id': booking.id, 'status': booking.status})
