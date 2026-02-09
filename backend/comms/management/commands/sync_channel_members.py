"""
Idempotent command to sync team chat channel membership:
- Delete messages sent by demo users
- Remove DM channels that only contain demo users
- Remove channels not relevant to NBNE (e.g. Stylists, Kitchen)
- Add all active staff to remaining non-DM channels
- Remove inactive / demo users from channels
"""
from django.core.management.base import BaseCommand
from comms.models import Channel, Message
from accounts.models import User
from staff.models import StaffProfile

# Channels that belong to NBNE (from seed_demo NBNE config)
NBNE_CHANNELS = {'General', 'Dev Team', 'Client Projects'}


class Command(BaseCommand):
    help = 'Sync team chat channel membership: add active staff, remove inactive/demo users'

    def handle(self, *args, **options):
        # 1. Delete ALL messages sent by demo users
        demo_msg_count = Message.objects.filter(sender__email__endswith='@demo.local').count()
        if demo_msg_count:
            Message.objects.filter(sender__email__endswith='@demo.local').delete()
            self.stdout.write(f'  Deleted {demo_msg_count} demo messages')

        # 2. Delete DM channels (demo-only)
        dm_channels = Channel.objects.filter(channel_type='DIRECT')
        if dm_channels.exists():
            count = dm_channels.count()
            dm_channels.delete()
            self.stdout.write(f'  Deleted {count} DM channels')

        # 3. Remove channels not in NBNE set (Stylists, Kitchen, Front Desk, Trainers, etc.)
        non_nbne = Channel.objects.exclude(name__in=NBNE_CHANNELS)
        if non_nbne.exists():
            names = list(non_nbne.values_list('name', flat=True))
            non_nbne.delete()
            self.stdout.write(f'  Removed non-NBNE channels: {", ".join(names)}')

        # 4. Sync remaining channels
        channels = Channel.objects.filter(is_archived=False)
        if not channels.exists():
            self.stdout.write('No channels found — skipping.')
            return

        # Active staff users (have an active StaffProfile)
        active_profiles = StaffProfile.objects.filter(is_active=True).select_related('user')
        active_users = [p.user for p in active_profiles]

        # Demo / inactive users to remove
        demo_users = User.objects.filter(email__endswith='@demo.local')
        inactive_users = User.objects.filter(is_active=False)
        users_to_remove = set(demo_users) | set(inactive_users)

        for ch in channels:
            for user in active_users:
                ch.members.add(user)
            for user in users_to_remove:
                ch.members.remove(user)
            member_count = ch.members.count()
            self.stdout.write(f'  #{ch.name}: {member_count} members')

        self.stdout.write(self.style.SUCCESS(f'Synced {channels.count()} channels.'))
