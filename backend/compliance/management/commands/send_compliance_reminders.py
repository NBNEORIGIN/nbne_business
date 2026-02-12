"""
Phase 6: Compliance reminders.
Sends email reminders for upcoming due dates and training expiry.
Trigger thresholds: 30 days, 7 days, 1 day before, and daily for overdue.
Run via: python manage.py send_compliance_reminders
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from compliance.models import ComplianceItem, TrainingRecord, ComplianceActionLog


THRESHOLDS = [30, 7, 1, 0]  # days before due


class Command(BaseCommand):
    help = 'Send compliance reminder emails for upcoming and overdue items'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview without sending')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        today = timezone.now().date()
        sent = 0

        self.stdout.write(f"[{timezone.now().isoformat()}] Running compliance reminders...")

        # --- Compliance items ---
        for threshold in THRESHOLDS:
            target_date = today + timedelta(days=threshold)
            items = ComplianceItem.objects.filter(
                next_due_date=target_date,
                responsible_user__isnull=False,
            ).select_related('responsible_user', 'category')

            for item in items:
                user = item.responsible_user
                if not user.email:
                    continue

                if threshold == 0:
                    subject = f"[DUE TODAY] {item.title}"
                    urgency = "is due TODAY"
                elif threshold < 0:
                    subject = f"[OVERDUE] {item.title}"
                    urgency = f"was due on {item.next_due_date}"
                else:
                    subject = f"[Reminder] {item.title} due in {threshold} days"
                    urgency = f"is due on {item.next_due_date} ({threshold} days)"

                body = (
                    f"Hi {user.first_name},\n\n"
                    f"Compliance item: {item.title}\n"
                    f"Category: {item.category.name}\n"
                    f"Status: {urgency}\n"
                    f"{'⚖️ This is a legal requirement.' if item.category.legal_requirement else ''}\n\n"
                    f"Please ensure this is completed on time.\n\n"
                    f"— NBNE Compliance System"
                )

                if dry_run:
                    self.stdout.write(f"  [DRY] Would email {user.email}: {subject}")
                else:
                    try:
                        send_mail(
                            subject, body,
                            settings.DEFAULT_FROM_EMAIL, [user.email],
                            fail_silently=True,
                        )
                        ComplianceActionLog.objects.create(
                            compliance_item=item, action='reminder_sent',
                            notes=f'Email reminder sent to {user.email} ({threshold}d threshold)',
                        )
                        sent += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  Failed to email {user.email}: {e}"))

        # --- Overdue items (daily reminder) ---
        overdue_items = ComplianceItem.objects.filter(
            status='overdue',
            responsible_user__isnull=False,
        ).select_related('responsible_user', 'category')

        for item in overdue_items:
            user = item.responsible_user
            if not user.email:
                continue

            subject = f"[OVERDUE] {item.title} — action required"
            body = (
                f"Hi {user.first_name},\n\n"
                f"This compliance item is OVERDUE:\n\n"
                f"Item: {item.title}\n"
                f"Category: {item.category.name}\n"
                f"Was due: {item.next_due_date}\n"
                f"{'⚖️ LEGAL REQUIREMENT — non-compliance may have regulatory consequences.' if item.category.legal_requirement else ''}\n\n"
                f"Please complete this urgently.\n\n"
                f"— NBNE Compliance System"
            )

            if dry_run:
                self.stdout.write(f"  [DRY] Overdue reminder → {user.email}: {subject}")
            else:
                try:
                    send_mail(
                        subject, body,
                        settings.DEFAULT_FROM_EMAIL, [user.email],
                        fail_silently=True,
                    )
                    sent += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Failed: {e}"))

        # --- Training expiry reminders ---
        for threshold in [30, 7, 1]:
            target_date = today + timedelta(days=threshold)
            records = TrainingRecord.objects.filter(
                expiry_date=target_date,
            ).select_related('user')

            for record in records:
                user = record.user
                if not user.email:
                    continue

                subject = f"[Training Expiry] {record.get_training_type_display()} expires in {threshold} days"
                body = (
                    f"Hi {user.first_name},\n\n"
                    f"Your {record.get_training_type_display()} training certificate "
                    f"expires on {record.expiry_date} ({threshold} days).\n\n"
                    f"Please arrange renewal.\n\n"
                    f"— NBNE Compliance System"
                )

                if dry_run:
                    self.stdout.write(f"  [DRY] Training reminder → {user.email}: {subject}")
                else:
                    try:
                        send_mail(
                            subject, body,
                            settings.DEFAULT_FROM_EMAIL, [user.email],
                            fail_silently=True,
                        )
                        sent += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  Failed: {e}"))

        prefix = '[DRY RUN] ' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(f"\n{prefix}Reminders complete: {sent} emails sent"))
