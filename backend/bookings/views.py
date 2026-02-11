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
    """Create a new booking (public). Supports both legacy TimeSlot and staff-aware direct booking."""
    serializer = BookingCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    checkout_url = None
    use_legacy = data.get('time_slot_id') is not None

    with db_transaction.atomic():
        service = Service.objects.get(id=data['service_id'])

        if use_legacy:
            # --- Legacy TimeSlot path ---
            time_slot = TimeSlot.objects.select_for_update().get(id=data['time_slot_id'])
            active_count = Booking.objects.filter(
                time_slot=time_slot
            ).exclude(status='CANCELLED').count()
            if active_count >= time_slot.max_bookings:
                return Response(
                    {'error': 'This time slot is no longer available.'},
                    status=status.HTTP_409_CONFLICT
                )
            booking_date = time_slot.date
            booking_time_val = time_slot.start_time
        else:
            # --- Staff-aware direct booking path ---
            time_slot = None
            booking_date = data['booking_date']
            booking_time_val = data['booking_time']
            staff_id = data.get('staff_id')

            # Validate no overlap with existing bookings for this staff member
            if staff_id:
                from datetime import datetime, timedelta
                slot_start = datetime.combine(booking_date, booking_time_val)
                slot_end = slot_start + timedelta(minutes=service.duration_minutes)
                overlapping = Booking.objects.filter(
                    assigned_staff_id=staff_id,
                    booking_date=booking_date,
                    status__in=['PENDING', 'PENDING_PAYMENT', 'CONFIRMED'],
                ).exclude(booking_time__isnull=True)
                for existing in overlapping:
                    ex_start = datetime.combine(existing.booking_date, existing.booking_time)
                    ex_end = ex_start + timedelta(minutes=existing.service.duration_minutes)
                    if slot_start < ex_end and slot_end > ex_start:
                        return Response(
                            {'error': 'This time slot is no longer available.'},
                            status=status.HTTP_409_CONFLICT
                        )

        # Calculate deposit: percentage takes priority over fixed amount
        if service.deposit_percentage and service.deposit_percentage > 0:
            deposit_pence = int(service.price_pence * service.deposit_percentage / 100)
        else:
            deposit_pence = service.deposit_pence
        needs_payment = deposit_pence > 0 and _payments_available()

        booking = Booking(
            customer_name=data['customer_name'],
            customer_email=data['customer_email'],
            customer_phone=data.get('customer_phone', ''),
            service=service,
            time_slot=time_slot,
            booking_date=booking_date,
            booking_time=booking_time_val,
            assigned_staff_id=data.get('staff_id'),
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
                        'slot_date': str(booking_date),
                        'slot_time': str(booking_time_val),
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
    bookings = Booking.objects.select_related('service', 'time_slot', 'assigned_staff').all()
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
@permission_classes([IsStaffOrAbove])
def mark_no_show(request, booking_id):
    """Mark a booking as no-show (staff+)."""
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    if booking.status not in ('CONFIRMED', 'PENDING'):
        return Response({'error': f'Cannot mark as no-show with status {booking.status}.'}, status=status.HTTP_400_BAD_REQUEST)
    booking.no_show()
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


@api_view(['DELETE'])
@permission_classes([IsManagerOrAbove])
def delete_booking(request, booking_id):
    """Permanently delete a booking (manager/owner only)."""
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    booking.delete()
    return Response({'deleted': True, 'id': booking_id})


@api_view(['POST'])
@permission_classes([IsStaffOrAbove])
def complete_booking(request, booking_id):
    """Mark a booking as completed (staff+)."""
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    if booking.status != 'CONFIRMED':
        return Response({'error': f'Cannot complete booking with status {booking.status}.'}, status=status.HTTP_400_BAD_REQUEST)
    booking.complete()
    return Response(BookingSerializer(booking).data)


@api_view(['POST'])
@permission_classes([IsStaffOrAbove])
def assign_staff(request, booking_id):
    """Assign a staff member to a booking (staff+)."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        booking = Booking.objects.select_related('service', 'time_slot').get(id=booking_id)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    staff_id = request.data.get('staff_id')
    if staff_id is None or staff_id == '' or staff_id == 0:
        booking.assigned_staff = None
        booking.save(update_fields=['assigned_staff', 'updated_at'])
        return Response(BookingSerializer(booking).data)
    try:
        staff_user = User.objects.get(id=int(staff_id))
    except (User.DoesNotExist, ValueError):
        return Response({'error': 'Staff member not found'}, status=status.HTTP_404_NOT_FOUND)
    booking.assigned_staff = staff_user
    booking.save(update_fields=['assigned_staff', 'updated_at'])
    return Response(BookingSerializer(booking).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def bookable_staff(request):
    """List staff members available for booking (public).
    Optional ?service_id= to filter by service (future: M2M)."""
    from .slot_utils import get_bookable_staff
    service_id = request.query_params.get('service_id')
    staff_list = get_bookable_staff(service_id)
    return Response(staff_list)


@api_view(['GET'])
@permission_classes([AllowAny])
def staff_slots(request):
    """Get available time slots for a specific staff member on a date (public).
    Required: ?staff_id=&service_id=&date=YYYY-MM-DD"""
    from .slot_utils import generate_staff_slots
    staff_id = request.query_params.get('staff_id')
    service_id = request.query_params.get('service_id')
    date_str = request.query_params.get('date')

    if not all([staff_id, service_id, date_str]):
        return Response({'error': 'staff_id, service_id, and date are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        slots = generate_staff_slots(int(staff_id), int(service_id), date_str)
    except (ValueError, Exception) as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'date': date_str, 'staff_id': int(staff_id), 'slots': slots})


@api_view(['GET'])
@permission_classes([AllowAny])
def disclaimer_check(request):
    """Check if a customer has a valid disclaimer on file.
    Required: ?email="""
    from .models import DisclaimerTemplate, ClientDisclaimer
    email = request.query_params.get('email', '').strip().lower()
    if not email:
        return Response({'error': 'email parameter required.'}, status=status.HTTP_400_BAD_REQUEST)

    active_templates = DisclaimerTemplate.objects.filter(is_active=True)
    if not active_templates.exists():
        return Response({'required': False, 'valid': True, 'message': 'No disclaimer required.'})

    template = active_templates.first()
    signature = ClientDisclaimer.objects.filter(
        customer_email__iexact=email,
        disclaimer=template,
        is_void=False,
    ).order_by('-signed_at').first()

    if signature and signature.is_valid:
        return Response({
            'required': True,
            'valid': True,
            'signed_at': signature.signed_at,
            'version': signature.version_signed,
        })

    return Response({
        'required': True,
        'valid': False,
        'disclaimer': {
            'id': template.id,
            'title': template.title,
            'body': template.body,
            'version': template.version,
        },
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def disclaimer_sign(request):
    """Sign a disclaimer form. Body: {email, name, disclaimer_id}"""
    from .models import DisclaimerTemplate, ClientDisclaimer
    email = request.data.get('email', '').strip().lower()
    name = request.data.get('name', '').strip()
    disclaimer_id = request.data.get('disclaimer_id')

    if not all([email, name, disclaimer_id]):
        return Response({'error': 'email, name, and disclaimer_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        template = DisclaimerTemplate.objects.get(id=disclaimer_id, is_active=True)
    except DisclaimerTemplate.DoesNotExist:
        return Response({'error': 'Disclaimer not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Get client IP
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    if ',' in ip:
        ip = ip.split(',')[0].strip()

    signature = ClientDisclaimer.objects.create(
        customer_email=email,
        customer_name=name,
        disclaimer=template,
        version_signed=template.version,
        ip_address=ip or None,
    )

    return Response({
        'signed': True,
        'signed_at': signature.signed_at,
        'version': signature.version_signed,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def disclaimer_void(request):
    """Void a client's disclaimer signature (manager+). Body: {email} or {signature_id}"""
    from .models import ClientDisclaimer
    email = request.data.get('email', '').strip().lower()
    sig_id = request.data.get('signature_id')

    if sig_id:
        try:
            sig = ClientDisclaimer.objects.get(id=sig_id)
            sig.is_void = True
            sig.save(update_fields=['is_void'])
            return Response({'voided': True, 'id': sig.id})
        except ClientDisclaimer.DoesNotExist:
            return Response({'error': 'Signature not found.'}, status=status.HTTP_404_NOT_FOUND)

    if email:
        count = ClientDisclaimer.objects.filter(customer_email__iexact=email, is_void=False).update(is_void=True)
        return Response({'voided': True, 'count': count})

    return Response({'error': 'email or signature_id required.'}, status=status.HTTP_400_BAD_REQUEST)


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


@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def booking_reports(request):
    """Reporting endpoint: daily takings, monthly takings, per-staff revenue.
    
    Query params:
      - report: 'daily' | 'monthly' | 'staff' | 'overview' (default: overview)
      - date_from: YYYY-MM-DD (default: 30 days ago)
      - date_to: YYYY-MM-DD (default: today)
      - staff_id: filter by assigned staff user ID
    """
    from django.db.models import Sum, Count, Avg, F, Case, When, Value, IntegerField
    from django.db.models.functions import TruncDate, TruncMonth
    from datetime import date as dt_date

    report_type = request.query_params.get('report', 'overview')
    today = timezone.now().date()

    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    try:
        date_from = dt_date.fromisoformat(date_from) if date_from else today - timedelta(days=30)
        date_to = dt_date.fromisoformat(date_to) if date_to else today
    except ValueError:
        return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

    base_qs = Booking.objects.filter(
        time_slot__date__gte=date_from,
        time_slot__date__lte=date_to,
    ).select_related('service', 'time_slot', 'assigned_staff')

    staff_id = request.query_params.get('staff_id')
    if staff_id:
        base_qs = base_qs.filter(assigned_staff_id=int(staff_id))

    # Completed bookings = revenue
    completed_qs = base_qs.filter(status__in=['COMPLETED', 'CONFIRMED'])
    no_show_qs = base_qs.filter(status='NO_SHOW')
    cancelled_qs = base_qs.filter(status='CANCELLED')

    if report_type == 'daily':
        rows = (
            completed_qs
            .values(day=F('time_slot__date'))
            .annotate(
                total_revenue=Sum('price_pence'),
                total_deposits=Sum('deposit_pence'),
                booking_count=Count('id'),
            )
            .order_by('day')
        )
        no_shows_by_day = dict(
            no_show_qs
            .values_list('time_slot__date')
            .annotate(cnt=Count('id'))
            .values_list('time_slot__date', 'cnt')
        )
        data = []
        for r in rows:
            data.append({
                'date': r['day'],
                'revenue_pence': r['total_revenue'] or 0,
                'deposits_pence': r['total_deposits'] or 0,
                'bookings': r['booking_count'],
                'no_shows': no_shows_by_day.get(r['day'], 0),
            })
        return Response({'report': 'daily', 'date_from': date_from, 'date_to': date_to, 'rows': data})

    elif report_type == 'monthly':
        rows = (
            completed_qs
            .annotate(month=TruncMonth('time_slot__date'))
            .values('month')
            .annotate(
                total_revenue=Sum('price_pence'),
                total_deposits=Sum('deposit_pence'),
                booking_count=Count('id'),
            )
            .order_by('month')
        )
        no_shows_monthly = dict(
            no_show_qs
            .annotate(month=TruncMonth('time_slot__date'))
            .values('month')
            .annotate(cnt=Count('id'))
            .values_list('month', 'cnt')
        )
        data = []
        for r in rows:
            data.append({
                'month': r['month'].strftime('%Y-%m') if r['month'] else None,
                'revenue_pence': r['total_revenue'] or 0,
                'deposits_pence': r['total_deposits'] or 0,
                'bookings': r['booking_count'],
                'no_shows': no_shows_monthly.get(r['month'], 0),
            })
        return Response({'report': 'monthly', 'date_from': date_from, 'date_to': date_to, 'rows': data})

    elif report_type == 'staff':
        rows = (
            completed_qs
            .filter(assigned_staff__isnull=False)
            .values('assigned_staff__id', 'assigned_staff__first_name', 'assigned_staff__last_name')
            .annotate(
                total_revenue=Sum('price_pence'),
                total_deposits=Sum('deposit_pence'),
                booking_count=Count('id'),
            )
            .order_by('-total_revenue')
        )
        no_shows_staff = dict(
            no_show_qs
            .filter(assigned_staff__isnull=False)
            .values('assigned_staff__id')
            .annotate(cnt=Count('id'))
            .values_list('assigned_staff__id', 'cnt')
        )
        data = []
        for r in rows:
            sid = r['assigned_staff__id']
            data.append({
                'staff_id': sid,
                'staff_name': f"{r['assigned_staff__first_name']} {r['assigned_staff__last_name']}".strip(),
                'revenue_pence': r['total_revenue'] or 0,
                'deposits_pence': r['total_deposits'] or 0,
                'bookings': r['booking_count'],
                'no_shows': no_shows_staff.get(sid, 0),
            })
        return Response({'report': 'staff', 'date_from': date_from, 'date_to': date_to, 'rows': data})

    else:  # overview
        total_bookings = base_qs.count()
        completed_count = completed_qs.count()
        no_show_count = no_show_qs.count()
        cancelled_count = cancelled_qs.count()
        agg = completed_qs.aggregate(
            total_revenue=Sum('price_pence'),
            total_deposits=Sum('deposit_pence'),
            avg_deposit_pct=Avg(
                Case(
                    When(price_pence__gt=0, then=F('deposit_pence') * 100.0 / F('price_pence')),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ),
        )
        return Response({
            'report': 'overview',
            'date_from': date_from,
            'date_to': date_to,
            'total_bookings': total_bookings,
            'completed': completed_count,
            'no_shows': no_show_count,
            'cancelled': cancelled_count,
            'no_show_rate': round(no_show_count / max(total_bookings, 1) * 100, 1),
            'revenue_pence': agg['total_revenue'] or 0,
            'deposits_pence': agg['total_deposits'] or 0,
            'avg_deposit_percentage': round(agg['avg_deposit_pct'] or 0, 1),
        })
