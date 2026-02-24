"""
Beta signup endpoint for the NBNE landing page.
Sends notification email to the team when someone signs up for the beta programme.
Uses same IONOS SMTP → Resend fallback chain as the contact form.
"""
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


logger = logging.getLogger(__name__)

ALLOWED_ORIGINS = [
    'https://business.nbne.uk',
    'https://nbne-landing.vercel.app',
    'http://localhost:3000',
]


def _cors_headers(request):
    origin = request.META.get('HTTP_ORIGIN', '')
    headers = {}
    if origin in ALLOWED_ORIGINS:
        headers['Access-Control-Allow-Origin'] = origin
        headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        headers['Access-Control-Allow-Headers'] = 'Content-Type'
        headers['Access-Control-Max-Age'] = '86400'
    return headers


def _add_cors(request, resp):
    for k, v in _cors_headers(request).items():
        resp[k] = v
    return resp


@csrf_exempt
def beta_signup(request):
    """
    POST { business_name, contact_name, email, phone, business_type, message }
    Sends a notification email to the NBNE team.
    """
    if request.method == 'OPTIONS':
        return _add_cors(request, JsonResponse({}, status=200))

    if request.method != 'POST':
        return _add_cors(request, JsonResponse({'error': 'Method not allowed'}, status=405))

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return _add_cors(request, JsonResponse({'error': 'Invalid JSON'}, status=400))

    business_name = (data.get('business_name') or '').strip()
    contact_name = (data.get('contact_name') or '').strip()
    email = (data.get('email') or '').strip()
    phone = (data.get('phone') or '').strip()
    business_type = (data.get('business_type') or '').strip()
    message = (data.get('message') or '').strip()

    if not business_name or not contact_name or not email:
        return _add_cors(request, JsonResponse(
            {'error': 'Business name, contact name, and email are required.'}, status=400
        ))

    subject = f'[NBNE Beta Signup] {business_name} — {contact_name}'
    text_body = f"""New beta programme signup from business.nbne.uk

Business:     {business_name}
Type:         {business_type or 'Not specified'}
Contact:      {contact_name}
Email:        {email}
Phone:        {phone or 'Not provided'}

Notes:
{message or 'None'}
"""

    to_email = 'toby@nbnesigns.com'
    sent = False

    # Method 1: IONOS SMTP
    smtp_host = getattr(settings, 'REMINDER_EMAIL_HOST', '')
    smtp_user = getattr(settings, 'REMINDER_EMAIL_HOST_USER', '')
    smtp_pass = getattr(settings, 'REMINDER_EMAIL_HOST_PASSWORD', '')
    smtp_port = getattr(settings, 'REMINDER_EMAIL_PORT', 465)
    smtp_ssl = getattr(settings, 'REMINDER_EMAIL_USE_SSL', True)
    from_email = getattr(settings, 'REMINDER_FROM_EMAIL', '') or smtp_user

    if smtp_host and smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f'NBNE Beta <{from_email}>'
            msg['To'] = to_email
            msg['Reply-To'] = email
            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))

            if smtp_ssl:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=5)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=5)
                server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, [to_email], msg.as_string())
            server.quit()
            sent = True
            logger.info(f'[BETA] Sent beta signup email for {business_name} ({email})')
        except Exception as e:
            logger.warning(f'[BETA] IONOS SMTP failed: {e}')

    # Method 2: Resend API
    resend_key = getattr(settings, 'RESEND_API_KEY', '')
    if resend_key and not sent:
        try:
            import resend
            resend.api_key = resend_key
            resend_from = getattr(settings, 'RESEND_FROM_EMAIL', 'onboarding@resend.dev')
            resend.Emails.send({
                "from": f"NBNE Beta <{resend_from}>",
                "to": [to_email],
                "reply_to": email,
                "subject": subject,
                "text": text_body,
            })
            sent = True
            logger.info(f'[BETA] Sent beta signup email via Resend for {business_name} ({email})')
        except Exception as e:
            logger.warning(f'[BETA] Resend failed: {e}')

    if not sent:
        logger.error(f'[BETA] Could not send beta signup email for {business_name} ({email})')
        return _add_cors(request, JsonResponse(
            {'error': 'Unable to submit. Please email us directly at toby@nbnesigns.com.'}, status=500
        ))

    return _add_cors(request, JsonResponse({
        'ok': True,
        'message': "You're on the list! We'll be in touch within 48 hours.",
    }))
