import json
import stripe
import requests
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from .models import Customer, PaymentSession, Transaction, Refund


stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session_internal(data):
    """Create a Stripe Checkout Session. Callable from Python (no HTTP needed)."""
    if not settings.PAYMENTS_ENABLED:
        raise ValueError('Payments are not enabled for this instance')

    payable_type = data.get('payable_type')
    payable_id = data.get('payable_id')
    amount_pence = data.get('amount_pence')
    currency = data.get('currency', settings.DEFAULT_CURRENCY)
    success_url = data.get('success_url')
    cancel_url = data.get('cancel_url')
    idempotency_key = data.get('idempotency_key')
    customer_data = data.get('customer', {})
    metadata = data.get('metadata', {})

    if not all([payable_type, payable_id, amount_pence, success_url, cancel_url, idempotency_key]):
        raise ValueError('Missing required fields')

    if amount_pence < 0:
        raise ValueError('Amount must be >= 0')

    with transaction.atomic():
        existing = PaymentSession.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            checkout_url = f"https://checkout.stripe.com/c/pay/{existing.stripe_checkout_session_id}" if existing.stripe_checkout_session_id else None
            return {'checkout_url': checkout_url, 'payment_session_id': str(existing.id), 'status': existing.status}

        customer = None
        if customer_data and customer_data.get('email'):
            customer, _ = Customer.objects.get_or_create(
                email=customer_data['email'],
                defaults={'name': customer_data.get('name', ''), 'phone': customer_data.get('phone', '')}
            )
            if not customer.provider_customer_id:
                try:
                    sc = stripe.Customer.create(email=customer.email, name=customer.name, phone=customer.phone)
                    customer.provider_customer_id = sc.id
                    customer.save(update_fields=['provider_customer_id'])
                except stripe.error.StripeError:
                    pass

        ps = PaymentSession.objects.create(
            payable_type=payable_type, payable_id=str(payable_id),
            amount_pence=amount_pence, currency=currency, status='created',
            customer=customer, success_url=success_url, cancel_url=cancel_url,
            metadata=metadata, idempotency_key=idempotency_key,
        )

        checkout_metadata = {'payable_type': payable_type, 'payable_id': str(payable_id), 'payment_session_id': str(ps.id)}
        checkout_metadata.update(metadata)

        params = {
            'payment_method_types': ['card'],
            'line_items': [{'price_data': {'currency': currency.lower(), 'unit_amount': amount_pence, 'product_data': {'name': f'{payable_type.title()} Payment'}}, 'quantity': 1}],
            'mode': 'payment', 'success_url': success_url, 'cancel_url': cancel_url, 'metadata': checkout_metadata,
        }
        if customer and customer.provider_customer_id:
            params['customer'] = customer.provider_customer_id

        cs = stripe.checkout.Session.create(**params)
        ps.stripe_checkout_session_id = cs.id
        ps.stripe_payment_intent_id = cs.payment_intent
        ps.status = 'pending'
        ps.save(update_fields=['stripe_checkout_session_id', 'stripe_payment_intent_id', 'status'])

        return {'checkout_url': cs.url, 'payment_session_id': str(ps.id), 'status': ps.status}


@csrf_exempt
@require_http_methods(["POST"])
def create_checkout_session(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    try:
        return JsonResponse(create_checkout_session_internal(data))
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except stripe.error.StripeError as e:
        return JsonResponse({'error': f'Stripe error: {str(e)}'}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    if not settings.STRIPE_WEBHOOK_SECRET:
        return JsonResponse({'error': 'Webhook secret not configured'}, status=500)
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    eid, etype = event['id'], event['type']
    if etype == 'checkout.session.completed':
        _handle_checkout_completed(event['data']['object'], eid)
    elif etype == 'payment_intent.succeeded':
        _handle_pi_succeeded(event['data']['object'], eid)
    elif etype == 'checkout.session.expired':
        _handle_checkout_expired(event['data']['object'], eid)
    elif etype == 'payment_intent.payment_failed':
        _handle_pi_failed(event['data']['object'], eid)
    elif etype == 'charge.refunded':
        _handle_charge_refunded(event['data']['object'], eid)
    return HttpResponse(status=200)


def _handle_checkout_completed(session, event_id):
    with transaction.atomic():
        ps = PaymentSession.objects.filter(stripe_checkout_session_id=session['id']).select_for_update().first()
        if not ps or not ps.mark_event_processed(event_id):
            return
        ps.status = 'succeeded'
        ps.stripe_payment_intent_id = session.get('payment_intent')
        ps.save(update_fields=['status', 'stripe_payment_intent_id', 'updated_at'])
        Transaction.objects.create(payment_session=ps, gross_amount_pence=ps.amount_pence, currency=ps.currency, provider_charge_id=session.get('payment_intent'))
        _trigger_callback(ps)


def _handle_pi_succeeded(pi, event_id):
    with transaction.atomic():
        ps = PaymentSession.objects.filter(stripe_payment_intent_id=pi['id']).select_for_update().first()
        if not ps or not ps.mark_event_processed(event_id):
            return
        if ps.status != 'succeeded':
            ps.status = 'succeeded'
            ps.save(update_fields=['status', 'updated_at'])
            if not ps.transactions.exists():
                Transaction.objects.create(payment_session=ps, gross_amount_pence=ps.amount_pence, currency=ps.currency, provider_charge_id=pi['id'])
            _trigger_callback(ps)


def _handle_checkout_expired(session, event_id):
    with transaction.atomic():
        ps = PaymentSession.objects.filter(stripe_checkout_session_id=session['id']).select_for_update().first()
        if not ps or not ps.mark_event_processed(event_id):
            return
        ps.status = 'canceled'
        ps.save(update_fields=['status', 'updated_at'])
        _trigger_callback(ps)


def _handle_pi_failed(pi, event_id):
    with transaction.atomic():
        ps = PaymentSession.objects.filter(stripe_payment_intent_id=pi['id']).select_for_update().first()
        if not ps or not ps.mark_event_processed(event_id):
            return
        ps.status = 'failed'
        ps.save(update_fields=['status', 'updated_at'])
        _trigger_callback(ps)


def _handle_charge_refunded(charge, event_id):
    with transaction.atomic():
        for txn in Transaction.objects.filter(provider_charge_id=charge['id']).select_for_update():
            ps = txn.payment_session
            if not ps.mark_event_processed(event_id):
                continue
            ps.status = 'refunded'
            ps.save(update_fields=['status', 'updated_at'])
            for rd in charge.get('refunds', {}).get('data', []):
                Refund.objects.get_or_create(
                    provider_refund_id=rd['id'],
                    defaults={'transaction': txn, 'amount_pence': rd['amount'], 'status': 'succeeded' if rd['status'] == 'succeeded' else 'failed', 'reason': rd.get('reason', '')}
                )
            _trigger_callback(ps)


def _trigger_callback(ps):
    if not settings.PAYMENTS_WEBHOOK_CALLBACK_URL:
        return
    try:
        requests.post(settings.PAYMENTS_WEBHOOK_CALLBACK_URL, json={'payable_type': ps.payable_type, 'payable_id': ps.payable_id, 'payment_session_id': str(ps.id), 'status': ps.status}, timeout=5)
    except Exception:
        pass


@require_http_methods(["GET"])
def get_payment_status(request, payment_session_id):
    try:
        ps = PaymentSession.objects.get(id=payment_session_id)
        return JsonResponse({'payment_session_id': str(ps.id), 'payable_type': ps.payable_type, 'payable_id': ps.payable_id, 'status': ps.status, 'amount_pence': ps.amount_pence, 'currency': ps.currency})
    except PaymentSession.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
