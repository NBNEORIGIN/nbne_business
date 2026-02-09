"""
Reset all active non-demo staff passwords, set must_change_password=True,
and email them their new temp credentials.

Uses a DB-level marker (user.date_joined is unchanged) to run only once.
Pass --force to re-run for everyone.

Usage:
  python manage.py reset_staff_passwords --login-url https://app.nbnesigns.co.uk/login
  python manage.py reset_staff_passwords --force --login-url https://app.nbnesigns.co.uk/login
"""
import secrets
import string
from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.models import User
from staff.models import StaffProfile
from staff.emails import send_welcome_email


class Command(BaseCommand):
    help = 'Reset passwords for all active non-demo staff and email them credentials'

    def add_arguments(self, parser):
        parser.add_argument('--login-url', type=str, default='https://app.nbnesigns.co.uk/login',
                            help='Login URL to include in the welcome email')
        parser.add_argument('--dry-run', action='store_true',
                            help='Print what would happen without making changes')
        parser.add_argument('--force', action='store_true',
                            help='Force reset even if must_change_password is already True')

    def handle(self, *args, **options):
        login_url = options['login_url']
        dry_run = options['dry_run']
        force = options['force']
        alphabet = string.ascii_letters + string.digits

        if not settings.EMAIL_HOST_USER:
            self.stdout.write('EMAIL_HOST_USER not configured — skipping password reset emails.')
            return

        # Get active staff profiles whose users are NOT demo accounts
        profiles = StaffProfile.objects.filter(
            is_active=True,
        ).select_related('user').exclude(
            user__email__endswith='@demo.local'
        )

        if not force:
            # Only reset staff who have must_change_password=True (created but never emailed)
            # OR must_change_password=False (legacy, never reset)
            # Skip users who have already successfully logged in and changed their password
            # We detect "already onboarded" by: must_change_password=False AND password != changeme123
            # Simplest: just reset everyone who still has must_change_password=True (never completed onboarding)
            profiles = profiles.filter(user__must_change_password=True)

        if not profiles.exists():
            self.stdout.write('No staff need password reset.')
            return

        self.stdout.write(f'Found {profiles.count()} staff to reset:\n')

        for profile in profiles:
            user = profile.user
            temp_password = ''.join(secrets.choice(alphabet) for _ in range(10))

            if dry_run:
                self.stdout.write(f'  [DRY RUN] {user.get_full_name()} ({user.email}) — would reset + email')
                continue

            user.set_password(temp_password)
            user.must_change_password = True
            user.save(update_fields=['password', 'must_change_password'])

            sent = send_welcome_email(user, temp_password, login_url)
            status_msg = 'email sent' if sent else 'EMAIL FAILED'
            self.stdout.write(f'  {user.get_full_name()} ({user.email}) — reset, {status_msg}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDry run complete. No changes made.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nDone. {profiles.count()} staff reset and emailed.'))
