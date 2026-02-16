"""
JWT Auth views for NBNE Business Platform.
Provides login, me, set-password, password-reset, and invite endpoints.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.conf import settings

from .models_auth import PasswordToken

logger = logging.getLogger(__name__)


def _get_role(user):
    """Determine role from user.role field, with fallback to Django flags."""
    if hasattr(user, 'role') and user.role in ('owner', 'manager', 'staff'):
        return user.role
    if user.is_superuser:
        return 'owner'
    elif user.is_staff:
        return 'manager'
    return 'staff'


def _send_token_email(to_email, to_name, token, purpose):
    """Send an invite or password-reset email with a secure link."""
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    brand_name = getattr(settings, 'EMAIL_BRAND_NAME', 'NBNE Business Platform')

    if purpose == 'invite':
        subject = f'Welcome to {brand_name} — Set Your Password'
        url = f'{frontend_url}/set-password?token={token}'
        heading = 'Welcome!'
        message = f'Hi {to_name}, your account has been created. Please click the button below to set your password and get started.'
        button_text = 'Set My Password'
    else:
        subject = f'{brand_name} — Password Reset'
        url = f'{frontend_url}/reset-password?token={token}'
        heading = 'Password Reset'
        message = f'Hi {to_name}, we received a request to reset your password. Click the button below to choose a new one.'
        button_text = 'Reset Password'

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<div style="max-width:520px;margin:0 auto;padding:20px;">
  <div style="background:#0f172a;border-radius:12px 12px 0 0;padding:24px 28px;text-align:center;">
    <h1 style="margin:0;color:#f8fafc;font-size:20px;font-weight:700;">{brand_name}</h1>
  </div>
  <div style="background:#ffffff;padding:28px;border-left:1px solid #e2e8f0;border-right:1px solid #e2e8f0;">
    <h2 style="margin:0 0 12px;color:#0f172a;font-size:18px;">{heading}</h2>
    <p style="margin:0 0 20px;color:#334155;font-size:15px;line-height:1.6;">{message}</p>
    <div style="text-align:center;margin:24px 0;">
      <a href="{url}" style="display:inline-block;padding:12px 32px;background:#6366f1;color:#ffffff;text-decoration:none;border-radius:8px;font-weight:700;font-size:15px;">{button_text}</a>
    </div>
    <p style="margin:0;color:#94a3b8;font-size:13px;">This link expires in 48 hours. If you didn't request this, you can safely ignore this email.</p>
    <p style="margin:12px 0 0;color:#94a3b8;font-size:12px;word-break:break-all;">Direct link: {url}</p>
  </div>
  <div style="background:#f1f5f9;border-radius:0 0 12px 12px;padding:16px 28px;border:1px solid #e2e8f0;border-top:none;">
    <p style="margin:0;color:#94a3b8;font-size:11px;text-align:center;">{brand_name} &middot; Secure account management</p>
  </div>
</div>
</body></html>"""

    text = f"""{heading}

{message}

{button_text}: {url}

This link expires in 48 hours. If you didn't request this, you can safely ignore this email.

{brand_name}"""

    # Try dedicated reminder SMTP first (IONOS), then Resend, then Django SMTP
    sent = False

    # Method 1: IONOS SMTP (reminder credentials)
    smtp_password = getattr(settings, 'REMINDER_EMAIL_HOST_PASSWORD', '')
    if smtp_password and not sent:
        try:
            host = getattr(settings, 'REMINDER_EMAIL_HOST', 'smtp.ionos.co.uk')
            port = getattr(settings, 'REMINDER_EMAIL_PORT', 465)
            use_ssl = getattr(settings, 'REMINDER_EMAIL_USE_SSL', True)
            user = getattr(settings, 'REMINDER_EMAIL_HOST_USER', '')
            from_email = getattr(settings, 'REMINDER_FROM_EMAIL', '')

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f'{brand_name} <{from_email}>'
            msg['To'] = to_email
            msg.attach(MIMEText(text, 'plain', 'utf-8'))
            msg.attach(MIMEText(html, 'html', 'utf-8'))

            if use_ssl:
                with smtplib.SMTP_SSL(host, port, timeout=15) as server:
                    server.login(user, smtp_password)
                    server.sendmail(from_email, [to_email], msg.as_string())
            else:
                with smtplib.SMTP(host, port, timeout=15) as server:
                    server.starttls()
                    server.login(user, smtp_password)
                    server.sendmail(from_email, [to_email], msg.as_string())
            sent = True
            logger.info(f'[AUTH] Sent {purpose} email via IONOS SMTP to {to_email}')
        except Exception as e:
            logger.warning(f'[AUTH] IONOS SMTP failed: {e}')

    # Method 2: Resend API
    resend_key = getattr(settings, 'RESEND_API_KEY', '')
    if resend_key and not sent:
        try:
            import resend
            resend.api_key = resend_key
            from_email = getattr(settings, 'RESEND_FROM_EMAIL', 'onboarding@resend.dev')
            resend.Emails.send({
                "from": f"{brand_name} <{from_email}>",
                "to": [to_email],
                "subject": subject,
                "html": html,
                "text": text,
            })
            sent = True
            logger.info(f'[AUTH] Sent {purpose} email via Resend to {to_email}')
        except Exception as e:
            logger.warning(f'[AUTH] Resend failed: {e}')

    if not sent:
        logger.error(f'[AUTH] Could not send {purpose} email to {to_email} — no working email provider')

    return sent


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    JWT login. Accepts { username, password }.
    Returns { access, refresh, user: { id, username, role, ... } }
    """
    username = request.data.get('username', '')
    password = request.data.get('password', '')

    user = authenticate(username=username, password=password)
    if user is None:
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    role = _get_role(user)

    refresh = RefreshToken.for_user(user)
    # Embed role and tenant in JWT so the frontend middleware can read it
    refresh['role'] = role
    refresh['name'] = f'{user.first_name} {user.last_name}'.strip() or user.username
    refresh['email'] = user.email
    refresh['tenant_slug'] = user.tenant.slug if user.tenant else ''

    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': role,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'must_change_password': not user.has_usable_password(),
            'tenant_slug': user.tenant.slug if user.tenant else '',
        },
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """Return current user info."""
    user = request.user
    role = _get_role(user)

    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': role,
        'is_superuser': user.is_superuser,
        'is_staff': user.is_staff,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_password_view(request):
    """Set new password for current user."""
    new_password = request.data.get('new_password', '')
    if len(new_password) < 6:
        return Response({'detail': 'Password must be at least 6 characters'}, status=status.HTTP_400_BAD_REQUEST)
    request.user.set_password(new_password)
    request.user.save()
    return Response({'ok': True})


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset_view(request):
    """
    POST { email } — Send a password reset link.
    Always returns 200 to prevent email enumeration.
    """
    email = request.data.get('email', '').strip().lower()
    if not email:
        return Response({'ok': True})  # Silent — no enumeration

    try:
        User = get_user_model()
        user = User.objects.get(email__iexact=email)
        token_obj = PasswordToken.create_for_user(user, purpose='reset', hours=48)
        _send_token_email(user.email, user.first_name or user.username, str(token_obj.token), 'reset')
    except User.DoesNotExist:
        pass  # Silent — no enumeration

    return Response({'ok': True, 'message': 'If an account exists with that email, a reset link has been sent.'})


@api_view(['GET'])
@permission_classes([AllowAny])
def validate_token_view(request):
    """
    GET ?token=<uuid> — Check if a token is valid.
    Returns { valid, purpose, email }
    """
    token_str = request.query_params.get('token', '')
    try:
        token_obj = PasswordToken.objects.get(token=token_str)
        if token_obj.is_valid():
            return Response({
                'valid': True,
                'purpose': token_obj.purpose,
                'email': token_obj.user.email,
                'name': token_obj.user.first_name or token_obj.user.username,
            })
        return Response({'valid': False, 'reason': 'Token has expired or already been used'})
    except (PasswordToken.DoesNotExist, ValueError):
        return Response({'valid': False, 'reason': 'Invalid token'})


@api_view(['POST'])
@permission_classes([AllowAny])
def set_password_with_token_view(request):
    """
    POST { token, new_password } — Set password using a valid token.
    Works for both invite and reset flows.
    """
    token_str = request.data.get('token', '')
    new_password = request.data.get('new_password', '')

    if len(new_password) < 8:
        return Response({'detail': 'Password must be at least 8 characters'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        token_obj = PasswordToken.objects.get(token=token_str)
    except (PasswordToken.DoesNotExist, ValueError):
        return Response({'detail': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

    if not token_obj.is_valid():
        return Response({'detail': 'Token has expired or already been used'}, status=status.HTTP_400_BAD_REQUEST)

    user = token_obj.user
    user.set_password(new_password)
    user.save()

    token_obj.used = True
    token_obj.save()

    # Return JWT tokens so the user is logged in immediately
    role = _get_role(user)
    refresh = RefreshToken.for_user(user)
    refresh['role'] = role
    refresh['name'] = f'{user.first_name} {user.last_name}'.strip() or user.username
    refresh['email'] = user.email

    return Response({
        'ok': True,
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': role,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
        },
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def send_invite_view(request):
    """
    POST { email } — Resend invite email for a user who hasn't set their password.
    Used by admins or the setup command.
    """
    email = request.data.get('email', '').strip().lower()
    try:
        User = get_user_model()
        user = User.objects.get(email__iexact=email)
        token_obj = PasswordToken.create_for_user(user, purpose='invite', hours=48)
        sent = _send_token_email(user.email, user.first_name or user.username, str(token_obj.token), 'invite')
        return Response({'ok': sent, 'message': 'Invite email sent' if sent else 'Failed to send email'})
    except User.DoesNotExist:
        return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
