"""Dedicated seed command for The Mind Department production instance.
Only seeds Mind Department tenant — no demo data, no other tenants."""
from datetime import date, time, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User


MIND_DEPARTMENT = {
    'business_name': 'The Mind Department',
    'tagline': 'Mindfulness for clarity, calm and sustainable performance',
    'colour_primary': '#8D9889',
    'colour_secondary': '#27382E',
    'colour_background': '#EEE8E5',
    'colour_text': '#27382E',
    'font_heading': 'RoxboroughCF, serif',
    'font_body': 'RoxboroughCF, serif',
    'font_url': 'https://fonts.cdnfonts.com/css/roxborough-cf',
    'email': 'contact@theminddepartment.com',
    'phone': '07395 812669',
    'address': '8 Park Road, Swarland, NE65 9JD',
    'website_url': 'https://www.theminddepartment.com',
    'social_instagram': 'https://instagram.com/aly.theminddepartment',
    'deposit_percentage': 50,
    'enabled_modules': ['bookings', 'payments', 'staff', 'compliance', 'documents', 'crm', 'analytics'],
    'services': [
        ('Mindful Movement & Meditation Class', 'Group Classes', 60, 1000, 0),
        ('Mindfulness Now 8-Week Group Course', 'Group Classes', 60, 20000, 10000),
        ('1:1 Mindfulness Session', 'One-to-one', 60, 6500, 3250),
        ('Workplace Wellbeing', 'Corporate', 60, 0, 0),
        ('Private Event Session', 'Events', 60, 0, 0),
    ],
    'disclaimer': {
        'title': 'Wellbeing Session Disclaimer',
        'body': (
            'The Mind Department offers wellness sessions designed to support your '
            'personal growth and wellbeing.\n\n'
            'Please note: Our sessions are not a substitute for medical or psychological '
            'treatment. If you have any medical concerns, please consult with a qualified '
            'healthcare professional.\n\n'
            'By proceeding, you confirm that you are participating in these sessions for '
            'wellness purposes and understand their supportive nature.\n\n'
            'You also confirm that you have read and accept our terms and conditions, and '
            'that you consent to The Mind Department storing your booking data in accordance '
            'with our privacy policy.\n\n'
            'This agreement is valid for 12 months from the date of signing.'
        ),
        'version': 1,
        'validity_days': 365,
    },
}


class Command(BaseCommand):
    help = 'Seed The Mind Department production data (idempotent)'

    def handle(self, *args, **options):
        self.stdout.write('=== Seeding The Mind Department (production) ===')

        # --- Cleanup stale data from any previous seed_demo runs ---
        self._cleanup_stale()

        # --- Owner user ---
        owner = self._create_user(
            'aly', 'contact@theminddepartment.com', 'Aly', 'Harwood', 'owner'
        )

        # --- Tenant settings ---
        self._seed_tenant()

        # --- Services ---
        self._seed_services()

        # --- Staff profile + working hours ---
        self._seed_staff(owner)

        # --- Disclaimer template ---
        self._seed_disclaimer()

        self.stdout.write(self.style.SUCCESS('\nMind Department seed complete!'))

    def _cleanup_stale(self):
        """Remove any stale data from previous seed_demo runs on this isolated instance."""
        from tenants.models import TenantSettings
        from bookings.models import Service, Booking, TimeSlot
        stale = TenantSettings.objects.exclude(slug='mind-department')
        if stale.exists():
            count = stale.count()
            stale.delete()
            self.stdout.write(f'  Cleaned up {count} stale tenant(s)')
        # Remove ALL bookings and timeslots (clean slate for production)
        bk_count = Booking.objects.all().count()
        if bk_count:
            Booking.objects.all().delete()
            self.stdout.write(f'  Cleaned up {bk_count} stale booking(s)')
        ts_count = TimeSlot.objects.all().count()
        if ts_count:
            TimeSlot.objects.all().delete()
            self.stdout.write(f'  Cleaned up {ts_count} stale timeslot(s)')
        # Remove services not belonging to Mind Department
        valid_names = {s[0] for s in MIND_DEPARTMENT['services']}
        stale_svcs = Service.objects.exclude(name__in=valid_names)
        if stale_svcs.exists():
            count = stale_svcs.count()
            stale_svcs.delete()
            self.stdout.write(f'  Cleaned up {count} stale service(s)')
        # Remove duplicate services (keep only one of each name)
        seen = set()
        for svc in Service.objects.order_by('id'):
            if svc.name in seen:
                svc.delete()
            else:
                seen.add(svc.name)
        # Remove stale demo users (not aly)
        stale_users = User.objects.exclude(username='aly').exclude(is_superuser=True)
        demo_usernames = ['owner', 'manager', 'staff1', 'staff2', 'customer1']
        deleted = stale_users.filter(username__in=demo_usernames).delete()[0]
        if deleted:
            self.stdout.write(f'  Cleaned up {deleted} stale demo user(s)')

    def _create_user(self, username, email, first, last, role):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email, 'first_name': first, 'last_name': last,
                'role': role, 'is_staff': True, 'is_superuser': role == 'owner',
            }
        )
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(f'  Created user: {username} (CHANGE PASSWORD IMMEDIATELY)')
        else:
            self.stdout.write(f'  User exists: {username}')
        return user

    def _seed_tenant(self):
        from tenants.models import TenantSettings
        cfg = MIND_DEPARTMENT
        defaults = {
            'business_name': cfg['business_name'],
            'tagline': cfg['tagline'],
            'colour_primary': cfg['colour_primary'],
            'colour_secondary': cfg['colour_secondary'],
            'colour_background': cfg['colour_background'],
            'colour_text': cfg['colour_text'],
            'font_heading': cfg['font_heading'],
            'font_body': cfg['font_body'],
            'font_url': cfg['font_url'],
            'email': cfg['email'],
            'phone': cfg['phone'],
            'address': cfg['address'],
            'website_url': cfg['website_url'],
            'social_instagram': cfg['social_instagram'],
            'currency': 'GBP',
            'currency_symbol': '£',
            'deposit_percentage': cfg['deposit_percentage'],
            'enabled_modules': cfg['enabled_modules'],
        }
        ts, created = TenantSettings.objects.update_or_create(
            slug='mind-department', defaults=defaults
        )
        self.stdout.write(f'  Tenant: {ts.business_name} ({"created" if created else "updated"})')

    def _seed_services(self):
        from bookings.models import Service
        for name, cat, dur, price, dep in MIND_DEPARTMENT['services']:
            Service.objects.update_or_create(
                name=name,
                defaults={
                    'category': cat,
                    'duration_minutes': dur,
                    'price_pence': price,
                    'deposit_pence': dep,
                }
            )
        self.stdout.write(f'  Services: {Service.objects.count()}')

    def _seed_staff(self, owner):
        from staff.models import StaffProfile, WorkingHours
        profile, _ = StaffProfile.objects.get_or_create(
            user=owner,
            defaults={
                'display_name': 'Aly Harwood',
                'phone': MIND_DEPARTMENT['phone'],
            }
        )
        # Mon-Fri 09:00-17:00
        for day in range(5):
            WorkingHours.objects.get_or_create(
                staff=profile, day_of_week=day,
                defaults={
                    'start_time': time(9, 0),
                    'end_time': time(17, 0),
                    'is_active': True,
                }
            )
        self.stdout.write(f'  Staff profile: Aly Harwood, working hours Mon-Fri 09-17')

    def _seed_disclaimer(self):
        from bookings.models import DisclaimerTemplate
        dcfg = MIND_DEPARTMENT['disclaimer']
        dt, created = DisclaimerTemplate.objects.get_or_create(
            title=dcfg['title'],
            defaults={
                'body': dcfg['body'],
                'version': dcfg['version'],
                'validity_days': dcfg['validity_days'],
                'is_active': True,
            }
        )
        self.stdout.write(
            f'  Disclaimer: {dt.title} v{dt.version} ({"created" if created else "exists"})'
        )
