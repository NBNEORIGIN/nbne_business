"""
Phase 2: Automated scheduling engine.
Daily management command to update compliance item statuses and training expiry.
Run via: python manage.py update_compliance_status
Schedule via cron or Railway scheduled task.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from compliance.models import ComplianceItem, TrainingRecord, ComplianceActionLog


class Command(BaseCommand):
    help = 'Update compliance item statuses based on due dates and training expiry'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview changes without saving')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        today = timezone.now().date()
        updated = 0
        overdue = 0
        due_soon = 0

        self.stdout.write(f"[{timezone.now().isoformat()}] Running compliance status update...")

        # --- Update ComplianceItem statuses ---
        items = ComplianceItem.objects.exclude(status='not_started').filter(next_due_date__isnull=False)

        for item in items:
            old_status = item.status
            item.update_status()

            if item.status != old_status:
                updated += 1
                if item.status == 'overdue':
                    overdue += 1
                elif item.status == 'due_soon':
                    due_soon += 1

                if not dry_run:
                    item.save(update_fields=['status', 'updated_at'])
                    ComplianceActionLog.objects.create(
                        compliance_item=item,
                        action='status_change',
                        notes=f'Auto-updated: {old_status} → {item.status}',
                    )

                self.stdout.write(f"  {item.title}: {old_status} → {item.status}")

        # --- Also check not_started items that now have a due date ---
        not_started = ComplianceItem.objects.filter(status='not_started', next_due_date__isnull=False)
        for item in not_started:
            item.update_status()
            if item.status != 'not_started':
                updated += 1
                if not dry_run:
                    item.save(update_fields=['status', 'updated_at'])
                    ComplianceActionLog.objects.create(
                        compliance_item=item,
                        action='status_change',
                        notes=f'Auto-updated: not_started → {item.status}',
                    )
                self.stdout.write(f"  {item.title}: not_started → {item.status}")

        # --- Summary ---
        prefix = '[DRY RUN] ' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f"\n{prefix}Status update complete: {updated} items changed "
            f"({overdue} overdue, {due_soon} due soon)"
        ))

        # --- Training expiry summary ---
        expired_training = TrainingRecord.objects.filter(expiry_date__lt=today).count()
        expiring_training = TrainingRecord.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=today + timedelta(days=30),
        ).count()

        if expired_training or expiring_training:
            self.stdout.write(self.style.WARNING(
                f"Training: {expired_training} expired, {expiring_training} expiring within 30 days"
            ))
