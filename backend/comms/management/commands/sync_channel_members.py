"""
One-time (idempotent) command to sync team chat channel membership:
- Add all active staff to all non-DM, non-archived channels
- Remove inactive / demo users from channels
"""
from django.core.management.base import BaseCommand
from comms.models import Channel
from accounts.models import User
from staff.models import StaffProfile


class Command(BaseCommand):
    help = 'Sync team chat channel membership: add active staff, remove inactive/demo users'

    def handle(self, *args, **options):
        channels = Channel.objects.filter(is_archived=False).exclude(channel_type='DIRECT')
        if not channels.exists():
            self.stdout.write('No channels found — skipping.')
            return

        # Active staff users (have an active StaffProfile)
        active_profiles = StaffProfile.objects.filter(is_active=True).select_related('user')
        active_users = [p.user for p in active_profiles]

        # Demo / inactive users to remove (demo.local emails or inactive User accounts)
        demo_users = User.objects.filter(email__endswith='@demo.local')
        inactive_users = User.objects.filter(is_active=False)
        users_to_remove = set(demo_users) | set(inactive_users)

        for ch in channels:
            # Add active staff
            for user in active_users:
                ch.members.add(user)
            # Remove demo/inactive
            for user in users_to_remove:
                ch.members.remove(user)
            member_count = ch.members.count()
            self.stdout.write(f'  #{ch.name}: {member_count} members')

        self.stdout.write(self.style.SUCCESS(f'Synced {channels.count()} channels.'))
