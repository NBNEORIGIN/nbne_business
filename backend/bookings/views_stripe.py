"""
Stripe Checkout integration for booking payments.
Creates a Stripe Checkout session when a booking is made,
redirects customer to pay, then confirms booking on success.
"""
import stripe
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Booking, Client, Service, Staff
from .models_payment import PaymentTransaction


@api_view(['POST'])
@permission_classes([AllowAny])
def create_checkout_session(request):
    """
    Create a Stripe Checkout session for a booking.
    Called by the frontend after booking details are collected.
    
    POST /api/checkout/create/
    Body: {
        "service_id": 2,
        "staff_id": 1,
        "date": "2026-02-16",
        "time": "11:00",
        "client_name": "...",
        "client_email": "...",
        "client_phone": "...",
        "notes": "..."
    }
    """
    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
    
    if not stripe.api_key:
        return Response(
            {'error': 'Payment system not configured'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    # Extract booking data (accept both naming conventions)
    service_id = request.data.get('service_id') or request.data.get('service')
    staff_id = request.data.get('staff_id') or request.data.get('staff')
    date_str = request.data.get('date') or request.data.get('booking_date')
    time_str = request.data.get('time') or request.data.get('booking_time')
    client_name = request.data.get('client_name') or request.data.get('customer_name', '')
    client_email = request.data.get('client_email') or request.data.get('customer_email', '')
    client_phone = request.data.get('client_phone') or request.data.get('customer_phone', '')
    notes = request.data.get('notes', '')
    
    if not all([service_id, staff_id, date_str, time_str, client_name, client_email]):
        return Response(
            {'error': 'Missing required booking fields'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        service = Service.objects.get(id=service_id)
        staff_member = Staff.objects.get(id=staff_id)
    except (Service.DoesNotExist, Staff.DoesNotExist):
        return Response(
            {'error': 'Invalid service or staff'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get or create client (scoped to tenant)
    tenant = getattr(request, 'tenant', None)
    client, _ = Client.objects.get_or_create(
        tenant=tenant, email=client_email,
        defaults={'name': client_name, 'phone': client_phone}
    )
    
    # Create booking in pending state
    from django.utils import timezone
    from datetime import datetime
    start_dt = timezone.make_aware(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M"))
    
    from datetime import timedelta
    end_dt = start_dt + timedelta(minutes=service.duration_minutes)
    booking = Booking.objects.create(
        tenant=tenant,
        client=client,
        service=service,
        staff=staff_member,
        start_time=start_dt,
        end_time=end_dt,
        status='pending',
        payment_status='pending',
        notes=notes,
    )
    
    # Calculate amount — use deposit if configured, otherwise full price
    full_pence = int(service.price * 100)
    if service.deposit_percentage and service.deposit_percentage > 0:
        amount_pence = int(full_pence * service.deposit_percentage / 100)
        payment_label = f'{service.name} — Deposit ({service.deposit_percentage}%)'
    elif service.deposit_pence and service.deposit_pence > 0:
        amount_pence = service.deposit_pence
        payment_label = f'{service.name} — Deposit'
    else:
        amount_pence = full_pence
        payment_label = service.name
    
    if amount_pence == 0:
        # Free service — confirm immediately
        booking.status = 'confirmed'
        booking.payment_status = 'paid'
        booking.payment_amount = 0
        booking.save()
        return Response({
            'free': True,
            'booking_id': booking.id,
            'status': 'confirmed',
        })
    
    # Create Stripe Checkout session
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {
                        'name': payment_label,
                        'description': f'{service.duration_minutes} min with {staff_member.name} on {date_str} at {time_str}',
                    },
                    'unit_amount': amount_pence,
                },
                'quantity': 1,
            }],
            mode='payment',
            customer_email=client_email,
            success_url=f'{frontend_url}/book?payment=success&booking_id={booking.id}',
            cancel_url=f'{frontend_url}/book?payment=cancelled&booking_id={booking.id}',
            metadata={
                'booking_id': str(booking.id),
                'service_name': service.name,
                'staff_name': staff_member.name,
            },
        )
        
        # Store session ID on booking
        booking.payment_id = checkout_session.id
        booking.payment_amount = service.price
        booking.save()
        
        # Create pending payment transaction
        PaymentTransaction.objects.create(
            client=client,
            transaction_type='single',
            status='pending',
            payment_system_id=checkout_session.id,
            amount=service.price,
            currency='GBP',
            payment_metadata={
                'booking_id': booking.id,
                'service': service.name,
                'staff': staff_member.name,
            },
        )
        
        return Response({
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id,
            'booking_id': booking.id,
        })
        
    except stripe.error.StripeError as e:
        booking.delete()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    """
    Stripe webhook endpoint.
    Confirms booking when payment succeeds, cancels on failure.
    
    POST /api/checkout/webhook/
    """
    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    
    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            import json
            event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        booking_id = session.get('metadata', {}).get('booking_id')
        payment_intent_id = session.get('payment_intent', session.get('id', ''))
        amount_total = session.get('amount_total', 0)  # in pence
        
        if booking_id:
            try:
                booking = Booking.objects.get(id=booking_id)
                booking.status = 'confirmed'
                booking.payment_status = 'paid'
                booking.payment_id = payment_intent_id
                booking.save()
                
                # Update existing pending transaction or create new one
                session_id = session.get('id', '')
                txn = PaymentTransaction.objects.filter(
                    payment_system_id=session_id
                ).first()
                
                if txn:
                    txn.status = 'completed'
                    txn.amount = amount_total / 100
                    txn.payment_metadata['payment_intent'] = payment_intent_id
                    txn.save()
                else:
                    PaymentTransaction.objects.create(
                        client=booking.client,
                        transaction_type='single',
                        status='completed',
                        payment_system_id=payment_intent_id,
                        amount=amount_total / 100,
                        currency=session.get('currency', 'gbp').upper(),
                        payment_metadata={
                            'booking_id': booking.id,
                            'service': booking.service.name,
                            'staff': booking.staff.name,
                            'stripe_session_id': session_id,
                        },
                    )
            except Booking.DoesNotExist:
                pass
    
    elif event['type'] == 'checkout.session.expired':
        session = event['data']['object']
        booking_id = session.get('metadata', {}).get('booking_id')
        
        if booking_id:
            try:
                booking = Booking.objects.get(id=booking_id)
                if booking.status == 'pending':
                    booking.status = 'cancelled'
                    booking.payment_status = 'failed'
                    booking.save()
                    
                    # Log failed payment
                    PaymentTransaction.objects.create(
                        client=booking.client,
                        transaction_type='single',
                        status='failed',
                        payment_system_id=session.get('id', f'expired_{booking_id}'),
                        amount=0,
                        currency='GBP',
                        payment_metadata={
                            'booking_id': booking.id,
                            'reason': 'checkout_expired',
                        },
                    )
            except Booking.DoesNotExist:
                pass
    
    return HttpResponse(status=200)
