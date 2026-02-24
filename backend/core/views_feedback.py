"""
Feedback endpoint — authenticated users can submit bug reports, feature ideas, or general feedback.
Sends notification email to the NBNE team with context (page, user, tenant).
"""
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def feedback_submit(request):
    """
    POST { type, message, page, user_agent }
    Sends feedback email to the NBNE team.
    """
    data = request.data
    fb_type = (data.get('type') or 'general').strip()
    message = (data.get('message') or '').strip()
    page = (data.get('page') or '').strip()
    user_agent = (data.get('user_agent') or '').strip()

    if not message:
        return Response({'error': 'Message is required.'}, status=400)

    user = request.user
    tenant = getattr(request, 'tenant', None)
    tenant_name = tenant.business_name if tenant else 'Unknown tenant'
    tenant_slug = tenant.slug if tenant else 'unknown'

    type_labels = {'bug': 'Bug Report', 'feature': 'Feature Request', 'general': 'General Feedback'}
    type_label = type_labels.get(fb_type, fb_type.title())

    subject = f'[NBNE Feedback] {type_label} — {tenant_name}'
    text_body = f"""New feedback from the admin panel

Type:       {type_label}
Tenant:     {tenant_name} ({tenant_slug})
User:       {user.first_name} {user.last_name} ({user.email})
Page:       {page or 'Not specified'}

Feedback:
{message}

---
User Agent: {user_agent or 'Not provided'}
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
            msg['From'] = f'NBNE Feedback <{from_email}>'
            msg['To'] = to_email
            msg['Reply-To'] = user.email
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
            logger.info(f'[FEEDBACK] Sent {fb_type} feedback from {user.email} ({tenant_slug})')
        except Exception as e:
            logger.warning(f'[FEEDBACK] IONOS SMTP failed: {e}')

    # Method 2: Resend API
    resend_key = getattr(settings, 'RESEND_API_KEY', '')
    if resend_key and not sent:
        try:
            import resend
            resend.api_key = resend_key
            resend_from = getattr(settings, 'RESEND_FROM_EMAIL', 'onboarding@resend.dev')
            resend.Emails.send({
                "from": f"NBNE Feedback <{resend_from}>",
                "to": [to_email],
                "reply_to": user.email,
                "subject": subject,
                "text": text_body,
            })
            sent = True
            logger.info(f'[FEEDBACK] Sent {fb_type} feedback via Resend from {user.email} ({tenant_slug})')
        except Exception as e:
            logger.warning(f'[FEEDBACK] Resend failed: {e}')

    if not sent:
        logger.error(f'[FEEDBACK] Could not send feedback from {user.email}')
        return Response({'error': 'Unable to send feedback right now. Please try again later.'}, status=500)

    return Response({'ok': True, 'message': 'Feedback sent. Thank you!'})
