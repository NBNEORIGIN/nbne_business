"""Email helpers for staff onboarding."""
from django.core.mail import send_mail
from django.conf import settings


def send_welcome_email(user, temp_password, login_url):
    """Send a welcome email to a new staff member with their login credentials."""
    subject = f'Welcome to {getattr(settings, "SITE_NAME", "the platform")} — Your Login Details'
    message = (
        f'Hi {user.first_name},\n\n'
        f'An account has been created for you.\n\n'
        f'Login URL: {login_url}\n'
        f'Email: {user.email}\n'
        f'Temporary Password: {temp_password}\n\n'
        f'You will be asked to set your own password when you first log in.\n\n'
        f'If you have any questions, please contact your manager.\n\n'
        f'Thanks,\n'
        f'The Team'
    )
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f'Failed to send welcome email to {user.email}: {e}')
        return False
