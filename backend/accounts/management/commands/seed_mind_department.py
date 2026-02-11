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
    'enabled_modules': ['bookings', 'payments', 'staff', 'compliance', 'documents'],
    'services': [
        ('Group Mindfulness Class', 'Group Classes', 60, 1200, 0),
        ('8-Week Group Mindfulness Course', 'Group Classes', 60, 8000, 4000),
        ('1:1 Mindfulness Session', 'One-to-one', 60, 5000, 2500),
        ('8-Week 1:1 Mindfulness Course', 'One-to-one', 60, 35000, 17500),
        ('Workplace Wellbeing Talk', 'Corporate', 60, 25000, 12500),
        ('Workplace Wellbeing Workshop', 'Corporate', 120, 45000, 22500),
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
            Service.objects.get_or_create(
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
