"""Management command to seed 3 exemplar demo tenants: Salon X, Restaurant X, Health Club X."""
from datetime import date, time, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User


TENANTS = {
    'salon-x': {
        'business_name': 'Salon X',
        'tagline': 'Premium Hair & Beauty',
        'colour_primary': '#2563eb',
        'colour_secondary': '#1e40af',
        'email': 'hello@salonx.demo',
        'phone': '07700 900000',
        'address': '123 High Street, London, E1 1AA',
        'deposit_percentage': 30,
        'enabled_modules': ['bookings', 'payments', 'staff', 'comms', 'compliance', 'documents', 'crm', 'analytics'],
        'services': [
            ('Cut & Style', 'Cuts', 45, 3500, 1000),
            ('Colour Full', 'Colour', 120, 9500, 2500),
            ('Balayage', 'Colour', 150, 14000, 4000),
            ('Blow Dry', 'Styling', 30, 2500, 0),
            ('Bridal Package', 'Special', 180, 25000, 7500),
            ('Gents Cut', 'Cuts', 30, 2000, 0),
        ],
        'comms_channels': [('General', 'GENERAL'), ('Stylists', 'TEAM')],
    },
    'restaurant-x': {
        'business_name': 'Restaurant X',
        'tagline': 'Fine Dining & Events',
        'colour_primary': '#b91c1c',
        'colour_secondary': '#7f1d1d',
        'email': 'hello@restaurantx.demo',
        'phone': '07700 900100',
        'address': '45 Market Square, Manchester, M1 2AB',
        'deposit_percentage': 20,
        'enabled_modules': ['bookings', 'payments', 'staff', 'comms', 'compliance', 'documents', 'crm', 'analytics'],
        'services': [
            ('Table for 2', 'Dining', 90, 0, 0),
            ('Table for 4', 'Dining', 120, 0, 0),
            ('Private Dining Room', 'Events', 180, 50000, 10000),
            ('Afternoon Tea', 'Experiences', 120, 4500, 1500),
            ('Chef\'s Table', 'Experiences', 150, 12000, 5000),
            ('Corporate Event', 'Events', 240, 200000, 50000),
        ],
        'comms_channels': [('General', 'GENERAL'), ('Kitchen', 'TEAM')],
    },
    'health-club-x': {
        'business_name': 'Health Club X',
        'tagline': 'Fitness, Wellness & Recovery',
        'colour_primary': '#059669',
        'colour_secondary': '#065f46',
        'email': 'hello@healthclubx.demo',
        'phone': '07700 900200',
        'address': '8 Riverside Park, Birmingham, B1 3CD',
        'deposit_percentage': 0,
        'enabled_modules': ['bookings', 'payments', 'staff', 'comms', 'compliance', 'documents', 'crm', 'analytics'],
        'services': [
            ('Personal Training', 'Training', 60, 5000, 1500),
            ('Group Class', 'Classes', 45, 1200, 0),
            ('Sports Massage', 'Wellness', 60, 5500, 1500),
            ('Swimming Lane', 'Facilities', 60, 800, 0),
            ('Sauna & Steam', 'Wellness', 90, 1500, 0),
            ('Physiotherapy', 'Medical', 45, 7500, 2000),
        ],
        'comms_channels': [('General', 'GENERAL'), ('Trainers', 'TEAM'), ('Front Desk', 'TEAM')],
    },
    'nbne': {
        'business_name': 'NBNE',
        'tagline': 'Business Technology & Consulting',
        'colour_primary': '#0f172a',
        'colour_secondary': '#1e293b',
        'email': 'hello@nbne.co.uk',
        'phone': '07700 900300',
        'address': 'Newcastle upon Tyne, UK',
        'deposit_percentage': 25,
        'enabled_modules': ['bookings', 'payments', 'staff', 'comms', 'compliance', 'documents', 'crm', 'analytics'],
        'services': [
            ('Discovery Workshop', 'Consulting', 120, 50000, 15000),
            ('Platform Setup', 'Onboarding', 240, 150000, 50000),
            ('Monthly Support', 'Support', 60, 25000, 0),
            ('Custom Integration', 'Development', 180, 100000, 30000),
            ('Training Session', 'Training', 90, 15000, 5000),
            ('Strategy Review', 'Consulting', 60, 30000, 10000),
        ],
        'comms_channels': [('General', 'GENERAL'), ('Dev Team', 'TEAM'), ('Client Projects', 'TEAM')],
    },
}


class Command(BaseCommand):
    help = 'Seed 3 exemplar demo tenants: Salon X, Restaurant X, Health Club X'

    def add_arguments(self, parser):
        parser.add_argument('--tenant', type=str, help='Seed only a specific tenant slug')

    def handle(self, *args, **options):
        target = options.get('tenant')
        slugs = [target] if target and target in TENANTS else list(TENANTS.keys())

        for slug in slugs:
            cfg = TENANTS[slug]
            self.stdout.write(f'\n=== Seeding {cfg["business_name"]} ({slug}) ===')

            # --- Users (shared across tenants for demo simplicity) ---
            owner = self._user('owner', 'jordan.riley@demo.local', 'Jordan', 'Riley', 'owner')
            manager = self._user('manager', 'alex.morgan@demo.local', 'Alex', 'Morgan', 'manager')
            staff1 = self._user('staff1', 'sam.kim@demo.local', 'Sam', 'Kim', 'staff')
            staff2 = self._user('staff2', 'taylor.chen@demo.local', 'Taylor', 'Chen', 'staff')
            customer = self._user('customer1', 'customer@demo.local', 'Jamie', 'Smith', 'customer')

            self._seed_tenant(slug, cfg)

            modules = cfg['enabled_modules']
            if 'bookings' in modules:
                self._seed_bookings(cfg, customer)
            if 'staff' in modules:
                self._seed_staff(cfg, owner, manager, staff1, staff2)
            if 'comms' in modules and cfg.get('comms_channels'):
                self._seed_comms(cfg, owner, manager, staff1, staff2)
            if 'compliance' in modules:
                self._seed_compliance(owner, staff1)
            if 'documents' in modules:
                self._seed_documents(owner, manager)
            if 'crm' in modules:
                self._seed_crm(owner, manager)

        self.stdout.write(self.style.SUCCESS('\nAll demo data seeded successfully!'))

    def _user(self, username, email, first, last, role):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email, 'first_name': first, 'last_name': last,
                'role': role, 'is_staff': role in ('owner', 'manager'),
            }
        )
        if created:
            user.set_password('admin123')
            user.save()
        else:
            # Ensure demo users are always active on re-seed
            changed = False
            if not user.is_active:
                user.is_active = True
                changed = True
            if user.role != role:
                user.role = role
                user.is_staff = role in ('owner', 'manager')
                changed = True
            if changed:
                user.save()
        return user

    def _seed_tenant(self, slug, cfg):
        from tenants.models import TenantSettings
        ts, created = TenantSettings.objects.update_or_create(
            slug=slug,
            defaults={
                'business_name': cfg['business_name'],
                'tagline': cfg['tagline'],
                'colour_primary': cfg['colour_primary'],
                'colour_secondary': cfg['colour_secondary'],
                'email': cfg['email'],
                'phone': cfg['phone'],
                'address': cfg['address'],
                'currency': 'GBP',
                'currency_symbol': '£',
                'deposit_percentage': cfg['deposit_percentage'],
                'enabled_modules': cfg['enabled_modules'],
            }
        )
        self.stdout.write(f'  Tenant: {ts.business_name} ({"created" if created else "updated"})')

    def _seed_bookings(self, cfg, customer):
        from bookings.models import Service, TimeSlot, Booking

        for name, cat, dur, price, dep in cfg['services']:
            Service.objects.get_or_create(
                name=name,
                defaults={'category': cat, 'duration_minutes': dur, 'price_pence': price, 'deposit_pence': dep}
            )
        self.stdout.write(f'  Services: {Service.objects.count()}')

        today = date.today()
        svc = Service.objects.first()
        for day_offset in range(7):
            d = today + timedelta(days=day_offset)
            if d.weekday() >= 6:
                continue
            for hour in range(9, 17):
                TimeSlot.objects.get_or_create(
                    date=d, start_time=time(hour, 0),
                    defaults={'end_time': time(hour + 1, 0), 'service': svc, 'max_bookings': 2}
                )
        self.stdout.write(f'  TimeSlots: {TimeSlot.objects.count()}')

        slots = list(TimeSlot.objects.all()[:5])
        statuses = ['CONFIRMED', 'PENDING', 'COMPLETED', 'CANCELLED', 'CONFIRMED']
        for slot, st in zip(slots, statuses):
            Booking.objects.get_or_create(
                customer_email=customer.email, time_slot=slot,
                defaults={
                    'customer_name': customer.get_full_name(),
                    'customer_phone': '07700 900001',
                    'service': svc, 'price_pence': svc.price_pence,
                    'deposit_pence': svc.deposit_pence, 'status': st,
                }
            )
        self.stdout.write(f'  Bookings: {Booking.objects.count()}')

    def _seed_staff(self, cfg, owner, manager, staff1, staff2):
        from staff.models import StaffProfile, Shift, LeaveRequest, TrainingRecord

        location = cfg['business_name']
        profiles = {}
        for user, name in [(owner, 'Jordan Riley'), (manager, 'Alex Morgan'), (staff1, 'Sam Kim'), (staff2, 'Taylor Chen')]:
            p, _ = StaffProfile.objects.get_or_create(
                user=user, defaults={'display_name': name, 'phone': user.email}
            )
            profiles[user.username] = p

        today = date.today()
        for p in profiles.values():
            for day_offset in range(5):
                d = today + timedelta(days=day_offset)
                Shift.objects.get_or_create(
                    staff=p, date=d, start_time=time(9, 0),
                    defaults={'end_time': time(17, 0), 'location': location, 'is_published': True}
                )

        LeaveRequest.objects.get_or_create(
            staff=profiles['staff1'], start_date=today + timedelta(days=10),
            defaults={'end_date': today + timedelta(days=12), 'leave_type': 'ANNUAL', 'reason': 'Holiday', 'status': 'PENDING'}
        )
        LeaveRequest.objects.get_or_create(
            staff=profiles['staff2'], start_date=today + timedelta(days=20),
            defaults={'end_date': today + timedelta(days=21), 'leave_type': 'SICK', 'reason': 'Medical appointment', 'status': 'APPROVED', 'reviewed_by': profiles['manager']}
        )

        TrainingRecord.objects.get_or_create(
            staff=profiles['staff1'], title='Fire Safety',
            defaults={'provider': 'SafetyFirst Ltd', 'completed_date': today - timedelta(days=60), 'expiry_date': today + timedelta(days=300)}
        )
        TrainingRecord.objects.get_or_create(
            staff=profiles['staff2'], title='COSHH Awareness',
            defaults={'provider': 'HSE Online', 'completed_date': today - timedelta(days=400), 'expiry_date': today - timedelta(days=35)}
        )
        self.stdout.write(f'  Staff profiles: {StaffProfile.objects.count()}, Shifts: {Shift.objects.count()}')

    def _seed_comms(self, cfg, owner, manager, staff1, staff2):
        from comms.models import Channel, Message

        channels = []
        for ch_name, ch_type in cfg['comms_channels']:
            ch, _ = Channel.objects.get_or_create(name=ch_name, defaults={'channel_type': ch_type, 'created_by': owner})
            ch.members.add(owner, manager, staff1, staff2)
            channels.append(ch)

        if channels and not Message.objects.filter(channel=channels[0]).exists():
            Message.objects.create(channel=channels[0], sender=owner, body='Welcome to the team chat!')
            Message.objects.create(channel=channels[0], sender=staff1, body='Thanks! Excited to be here.')
            Message.objects.create(channel=channels[0], sender=manager, body='Remember to check the rota for next week.')
        self.stdout.write(f'  Channels: {Channel.objects.count()}, Messages: {Message.objects.count()}')

    def _seed_compliance(self, owner, staff1):
        from compliance.models import IncidentReport, RAMSDocument

        IncidentReport.objects.get_or_create(
            title='Wet floor slip hazard',
            defaults={
                'description': 'Water pooling near wash stations during busy period.',
                'severity': 'MEDIUM', 'status': 'INVESTIGATING', 'location': 'Wash Area',
                'incident_date': timezone.now() - timedelta(days=3), 'reported_by': staff1,
            }
        )
        IncidentReport.objects.get_or_create(
            title='Chemical storage unlabelled',
            defaults={
                'description': 'Several COSHH substances found without proper labels.',
                'severity': 'HIGH', 'status': 'OPEN', 'location': 'Store Room',
                'incident_date': timezone.now() - timedelta(days=1), 'reported_by': staff1,
            }
        )
        RAMSDocument.objects.get_or_create(
            title='General Risk Assessment',
            defaults={
                'reference_number': 'RAMS-001', 'description': 'General risk assessment for operations.',
                'status': 'ACTIVE', 'issue_date': date.today() - timedelta(days=90),
                'expiry_date': date.today() + timedelta(days=275), 'created_by': owner,
            }
        )
        self.stdout.write(f'  Incidents: {IncidentReport.objects.count()}, RAMS: {RAMSDocument.objects.count()}')

    def _seed_documents(self, owner, manager):
        from documents.models import DocumentTag

        for tag_name in ['Policy', 'HSE', 'Training', 'HR']:
            DocumentTag.objects.get_or_create(name=tag_name)
        self.stdout.write(f'  Document tags: {DocumentTag.objects.count()}')

    def _seed_crm(self, owner, manager):
        from crm.models import Lead

        leads_data = [
            ('Emma Wilson', 'emma@example.com', 'WEBSITE', 'CONVERTED', 15000),
            ('Liam Brown', 'liam@example.com', 'REFERRAL', 'QUALIFIED', 8000),
            ('Sophia Davis', 'sophia@example.com', 'SOCIAL', 'NEW', 5000),
            ('Noah Taylor', 'noah@example.com', 'WALK_IN', 'CONTACTED', 12000),
            ('Olivia Jones', 'olivia@example.com', 'PHONE', 'LOST', 3000),
        ]
        for name, email, source, status, value in leads_data:
            Lead.objects.get_or_create(
                email=email,
                defaults={'name': name, 'source': source, 'status': status, 'value_pence': value, 'created_by': owner}
            )
        self.stdout.write(f'  Leads: {Lead.objects.count()}')
