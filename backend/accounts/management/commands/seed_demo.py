"""Management command to seed 3 exemplar demo tenants: Salon X, Restaurant X, Health Club X."""
from datetime import date, time, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


TENANTS = {
    'salon-x': {
        'business_type': 'salon',
        'business_name': 'Salon X',
        'tagline': 'Premium Hair & Beauty',
        'colour_primary': '#2563eb',
        'colour_secondary': '#1e40af',
        'email': 'hello@salonx.demo',
        'phone': '07700 900000',
        'address': '123 High Street, London, E1 1AA',
        'deposit_percentage': 30,
        'booking_staff_label': 'Stylist',
        'booking_staff_label_plural': 'Stylists',
        'enabled_modules': ['bookings', 'payments', 'staff', 'comms', 'compliance', 'documents', 'crm', 'analytics'],
        'services': [
            ('Cut & Style', 'Cuts', 45, '35.00', 1000),
            ('Colour Full', 'Colour', 120, '95.00', 2500),
            ('Balayage', 'Colour', 150, '140.00', 4000),
            ('Blow Dry', 'Styling', 30, '25.00', 0),
            ('Bridal Package', 'Special', 180, '250.00', 7500),
            ('Gents Cut', 'Cuts', 30, '20.00', 0),
        ],
        'booking_staff': [
            ('chloe@salonx.demo', 'Chloe Williams', 'staff', ['Cut & Style', 'Colour Full', 'Balayage', 'Blow Dry', 'Bridal Package'], '12:00', '12:30'),
            ('jordan@salonx.demo', 'Jordan Taylor', 'staff', ['Cut & Style', 'Blow Dry', 'Gents Cut'], '12:00', '12:30'),
            ('Mia@salonx.demo', 'Mia Patel', 'staff', ['Colour Full', 'Balayage', 'Blow Dry', 'Bridal Package'], '13:00', '13:30'),
        ],
        'demo_clients': [
            ('Alice Hartley', 'alice.h@example.com', '07700 100001'),
            ('Ben Cooper', 'ben.c@example.com', '07700 100002'),
            ('Charlotte Reed', 'charlotte.r@example.com', '07700 100003'),
            ('Dylan Foster', 'dylan.f@example.com', '07700 100004'),
            ('Emily Watson', 'emily.w@example.com', '07700 100005'),
            ('Finn O\'Reilly', 'finn.or@example.com', '07700 100006'),
            ('Grace Liu', 'grace.l@example.com', '07700 100007'),
            ('Harry Blackwell', 'harry.b@example.com', '07700 100008'),
            ('Isla Campbell', 'isla.c@example.com', '07700 100009'),
            ('Jack Thornton', 'jack.t@example.com', '07700 100010'),
        ],
        'comms_channels': [('General', 'GENERAL'), ('Stylists', 'TEAM')],
    },
    'restaurant-x': {
        'business_type': 'restaurant',
        'business_name': 'Tavola',
        'tagline': 'Fine Dining & Events',
        'colour_primary': '#059669',
        'colour_secondary': '#065f46',
        'email': 'hello@tavola.demo',
        'phone': '07700 900100',
        'address': '45 Market Square, Manchester, M1 2AB',
        'deposit_percentage': 20,
        'booking_staff_label': 'Host',
        'booking_staff_label_plural': 'Hosts',
        'enabled_modules': ['bookings', 'payments', 'staff', 'comms', 'compliance', 'documents', 'crm', 'analytics'],
        'services': [
            ('Book a Table', 'Reservations', 90, '0.00', 500),
            ('Table for 4-6', 'Reservations', 120, '0.00', 1000),
            ('Large Party (7+)', 'Reservations', 150, '0.00', 2000),
            ('Afternoon Tea for 2', 'Experiences', 120, '55.00', 1500),
            ('Chef\'s Table (6 Course Tasting)', 'Experiences', 180, '150.00', 5000),
            ('Private Dining Room', 'Events', 180, '500.00', 15000),
        ],
        'booking_staff': [
            ('marco@tavola.demo', 'Marco Rossi', 'manager',
             ['Book a Table', 'Table for 4-6', 'Large Party (7+)',
              'Afternoon Tea for 2'],
             '15:00', '16:00'),
            ('elena@tavola.demo', 'Elena Marchetti', 'staff',
             ['Book a Table', 'Table for 4-6', 'Large Party (7+)',
              'Afternoon Tea for 2'],
             '15:00', '16:00'),
            ('chef.luca@tavola.demo', 'Chef Luca De Luca', 'staff',
             ['Chef\'s Table (6 Course Tasting)', 'Private Dining Room'],
             '15:30', '16:00'),
        ],
        'demo_clients': [
            ('Sophie Turner', 'sophie.t@example.com', '07700 800001'),
            ('David Mitchell', 'david.m@example.com', '07700 800002'),
            ('Rachel Green', 'rachel.g@example.com', '07700 800003'),
            ('Tom Hardy', 'tom.h@example.com', '07700 800004'),
            ('Lucy Chen', 'lucy.c@example.com', '07700 800005'),
            ('Mark Williams', 'mark.w@example.com', '07700 800006'),
            ('Priya Sharma', 'priya.s@example.com', '07700 800007'),
            ('James O\'Brien', 'james.ob@example.com', '07700 800008'),
            ('Hannah Baker', 'hannah.b@example.com', '07700 800009'),
            ('Oliver Stone', 'oliver.s@example.com', '07700 800010'),
            ('Emma Woodhouse', 'emma.w@example.com', '07700 800011'),
            ('Daniel Craig', 'daniel.c@example.com', '07700 800012'),
        ],
        'comms_channels': [('General', 'GENERAL'), ('Kitchen', 'TEAM'), ('Front of House', 'TEAM')],
    },
    'health-club-x': {
        'business_type': 'gym',
        'business_name': 'FitHub',
        'tagline': 'Fitness, Wellness & Recovery',
        'colour_primary': '#dc2626',
        'colour_secondary': '#991b1b',
        'email': 'hello@fithub.demo',
        'phone': '07700 900200',
        'address': '8 Riverside Park, Birmingham, B1 3CD',
        'deposit_percentage': 0,
        'booking_staff_label': 'Trainer',
        'booking_staff_label_plural': 'Trainers',
        'enabled_modules': ['bookings', 'payments', 'staff', 'comms', 'compliance', 'documents', 'crm', 'analytics'],
        'services': [
            # Memberships
            ('Monthly Membership', 'Memberships', 30, '49.99', 0),
            ('6-Month Membership', 'Memberships', 30, '269.99', 5000),
            ('Annual Membership', 'Memberships', 30, '479.99', 10000),
            ('Student Monthly', 'Memberships', 30, '29.99', 0),
            # Personal Training
            ('1:1 Personal Training', 'Personal Training', 60, '50.00', 1500),
            ('PT Block (5 Sessions)', 'Personal Training', 60, '225.00', 5000),
            ('PT Block (10 Sessions)', 'Personal Training', 60, '400.00', 10000),
            ('Couples PT Session', 'Personal Training', 60, '75.00', 2000),
            # Classes
            ('HIIT Class', 'Classes', 45, '12.00', 0),
            ('Yoga Flow', 'Classes', 60, '12.00', 0),
            ('Spin Class', 'Classes', 45, '12.00', 0),
            ('Boxing Fitness', 'Classes', 45, '14.00', 0),
            ('Pilates', 'Classes', 60, '12.00', 0),
            ('CrossFit WOD', 'Classes', 60, '15.00', 0),
            # Wellness
            ('Sports Massage', 'Wellness', 60, '55.00', 1500),
            ('Physiotherapy', 'Wellness', 45, '75.00', 2000),
            ('Sauna & Steam Room', 'Wellness', 90, '15.00', 0),
            ('Swimming Lane Booking', 'Facilities', 60, '8.00', 0),
        ],
        'booking_staff': [
            ('jake@fithub.demo', 'Jake Morrison', 'staff',
             ['1:1 Personal Training', 'PT Block (5 Sessions)', 'PT Block (10 Sessions)',
              'Couples PT Session', 'HIIT Class', 'Boxing Fitness', 'CrossFit WOD'],
             '12:00', '12:30'),
            ('sarah@fithub.demo', 'Sarah Okonkwo', 'staff',
             ['1:1 Personal Training', 'PT Block (5 Sessions)', 'PT Block (10 Sessions)',
              'Couples PT Session', 'Yoga Flow', 'Pilates'],
             '13:00', '13:30'),
            ('ryan@fithub.demo', 'Ryan Patel', 'staff',
             ['Spin Class', 'HIIT Class', 'CrossFit WOD', 'Boxing Fitness'],
             '12:00', '12:30'),
            ('lisa@fithub.demo', 'Lisa Nguyen', 'staff',
             ['Sports Massage', 'Physiotherapy'],
             '12:30', '13:00'),
        ],
        'demo_clients': [
            ('Chris Evans', 'chris.e@example.com', '07700 900301'),
            ('Amy Johnson', 'amy.j@example.com', '07700 900302'),
            ('Ben Taylor', 'ben.t@example.com', '07700 900303'),
            ('Zara Khan', 'zara.k@example.com', '07700 900304'),
            ('Mike O\'Donnell', 'mike.od@example.com', '07700 900305'),
            ('Freya Larsson', 'freya.l@example.com', '07700 900306'),
            ('Sam Okafor', 'sam.ok@example.com', '07700 900307'),
            ('Katie Price', 'katie.p@example.com', '07700 900308'),
            ('Dan Wilson', 'dan.w@example.com', '07700 900309'),
            ('Megan Fox', 'megan.f@example.com', '07700 900310'),
            ('Raj Patel', 'raj.p@example.com', '07700 900311'),
            ('Isla Murray', 'isla.m@example.com', '07700 900312'),
            ('Luke Brennan', 'luke.b@example.com', '07700 900313'),
            ('Nina Petrova', 'nina.p@example.com', '07700 900314'),
            ('Oscar Lee', 'oscar.l@example.com', '07700 900315'),
        ],
        'comms_channels': [('General', 'GENERAL'), ('Trainers', 'TEAM'), ('Front Desk', 'TEAM')],
    },
    'mind-department': {
        'business_type': 'generic',
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
            ('Mindful Movement & Meditation Class', 'Group Classes', 60, '10.00', 0),
            ('Mindfulness Now 8-Week Group Course', 'Group Classes', 60, '200.00', 10000),
            ('1:1 Mindfulness Session', 'One-to-one', 60, '65.00', 3250),
            ('Workplace Wellbeing', 'Corporate', 60, '0.00', 0),
            ('Private Event Session', 'Events', 60, '0.00', 0),
        ],
        'comms_channels': [],
        'staff_users': [
            ('aly', 'contact@theminddepartment.com', 'Aly', 'Harwood', 'owner'),
        ],
        'disclaimer': {
            'title': 'Wellbeing Session Disclaimer',
            'body': 'The Mind Department offers wellness sessions designed to support your personal growth and wellbeing.\n\nPlease note: Our sessions are not a substitute for medical or psychological treatment. If you have any medical concerns, please consult with a qualified healthcare professional.\n\nBy proceeding, you confirm that you are participating in these sessions for wellness purposes and understand their supportive nature.\n\nYou also confirm that you have read and accept our terms and conditions, and that you consent to The Mind Department storing your booking data in accordance with our privacy policy.\n\nThis agreement is valid for 12 months from the date of signing.',
            'version': 1,
            'validity_days': 365,
        },
    },
    'nbne': {
        'business_type': 'generic',
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
            ('Discovery Workshop', 'Consulting', 120, '500.00', 15000),
            ('Platform Setup', 'Onboarding', 240, '1500.00', 50000),
            ('Monthly Support', 'Support', 60, '250.00', 0),
            ('Custom Integration', 'Development', 180, '1000.00', 30000),
            ('Training Session', 'Training', 90, '150.00', 5000),
            ('Strategy Review', 'Consulting', 60, '300.00', 10000),
        ],
        'comms_channels': [('General', 'GENERAL'), ('Dev Team', 'TEAM'), ('Client Projects', 'TEAM')],
        'staff_users': [
            ('toby', 'toby@nbnesigns.com', 'Toby', 'Fletcher', 'owner'),
            ('jo', 'jo@nbnesigns.com', 'Jo', 'Tompkins', 'manager'),
            ('gabby', 'gabby@nbnesigns.com', 'Gabby', 'Bassett', 'staff'),
            ('ben', 'ben@nbnesigns.com', 'Ben', 'Randall', 'staff'),
            ('ivan', 'ivan@nbnesigns.com', 'Ivan', 'Fillippov', 'staff'),
            ('sanna', 'sanna@nbnesigns.com', 'Sanna', 'Mager-Brink', 'staff'),
        ],
    },
}


class Command(BaseCommand):
    help = 'Seed demo tenants with isolated per-tenant data'

    def add_arguments(self, parser):
        parser.add_argument('--tenant', type=str, help='Seed only a specific tenant slug')
        parser.add_argument('--delete-demo', action='store_true', help='Delete all demo data for the specified tenant(s)')

    def handle(self, *args, **options):
        from tenants.models import TenantSettings
        target = options.get('tenant')
        slugs = [target] if target and target in TENANTS else list(TENANTS.keys())

        if options.get('delete_demo'):
            self._delete_demo(slugs)
            return

        for slug in slugs:
            cfg = TENANTS[slug]
            self.stdout.write(f'\n=== Seeding {cfg["business_name"]} ({slug}) ===')

            # --- Create/update tenant ---
            self.tenant = self._seed_tenant(slug, cfg)

            # --- Per-tenant users (unique usernames per tenant) ---
            owner = self._user(f'{slug}-owner', f'owner@{slug}.demo', 'Jordan', 'Riley', 'owner')
            manager = self._user(f'{slug}-manager', f'manager@{slug}.demo', 'Alex', 'Morgan', 'manager')
            staff1 = self._user(f'{slug}-staff1', f'staff1@{slug}.demo', 'Sam', 'Kim', 'staff')
            staff2 = self._user(f'{slug}-staff2', f'staff2@{slug}.demo', 'Taylor', 'Chen', 'staff')
            customer = self._user(f'{slug}-customer', f'customer@{slug}.demo', 'Jamie', 'Smith', 'customer')

            # Create tenant-specific staff users if configured (e.g. Mind Department, NBNE)
            if cfg.get('staff_users'):
                for uname, uemail, ufirst, ulast, urole in cfg['staff_users']:
                    u = self._user(uname, uemail, ufirst, ulast, urole)
                    self.stdout.write(f'  Tenant user: {uname} ({urole})')
                    if urole == 'owner':
                        owner = u

            # Seed disclaimer if configured
            if cfg.get('disclaimer'):
                self._seed_disclaimer(cfg['disclaimer'])

            modules = cfg['enabled_modules']
            if 'bookings' in modules:
                self._seed_bookings(cfg, customer)
            if 'staff' in modules:
                if cfg.get('staff_users'):
                    self._seed_staff_custom(cfg)
                else:
                    self._seed_staff(cfg, owner, manager, staff1, staff2)
            if 'comms' in modules and cfg.get('comms_channels'):
                self._seed_comms(slug, cfg, owner, manager, staff1, staff2)
            if 'compliance' in modules:
                self._seed_compliance(owner, staff1)
            if 'documents' in modules:
                self._seed_documents(owner, manager)
            if 'crm' in modules:
                self._seed_crm(owner, manager)

        self.stdout.write(self.style.SUCCESS('\nAll demo data seeded successfully!'))

    def _delete_demo(self, slugs):
        """Delete all demo data for the specified tenant slugs."""
        from tenants.models import TenantSettings
        for slug in slugs:
            try:
                tenant = TenantSettings.objects.get(slug=slug)
            except TenantSettings.DoesNotExist:
                self.stdout.write(f'  Tenant {slug} not found — skipping')
                continue
            self.stdout.write(f'\n=== Deleting demo data for {tenant.business_name} ({slug}) ===')
            # Delete in dependency order (children first)
            models_to_clear = []
            try:
                from staff.models import TimesheetEntry, WorkingHours, Shift, LeaveRequest, TrainingRecord, ProjectCode, StaffProfile
                models_to_clear += [
                    ('TimesheetEntry', TimesheetEntry.objects.filter(staff__tenant=tenant)),
                    ('WorkingHours', WorkingHours.objects.filter(staff__tenant=tenant)),
                    ('Shift', Shift.objects.filter(staff__tenant=tenant)),
                    ('LeaveRequest', LeaveRequest.objects.filter(staff__tenant=tenant)),
                    ('TrainingRecord', TrainingRecord.objects.filter(staff__tenant=tenant)),
                    ('ProjectCode', ProjectCode.objects.filter(tenant=tenant)),
                    ('StaffProfile', StaffProfile.objects.filter(tenant=tenant)),
                ]
            except Exception:
                pass
            try:
                from bookings.models import Booking, Client, Service
                from bookings.models import Staff as BookingStaff
                models_to_clear += [
                    ('Booking', Booking.objects.filter(tenant=tenant)),
                    ('Client', Client.objects.filter(tenant=tenant)),
                    ('BookingStaff', BookingStaff.objects.filter(tenant=tenant)),
                    ('Service', Service.objects.filter(tenant=tenant)),
                ]
            except Exception:
                pass
            try:
                from comms.models import Message, ChannelMember, Channel
                for ch in Channel.objects.filter(tenant=tenant):
                    Message.objects.filter(channel=ch).delete()
                    ChannelMember.objects.filter(channel=ch).delete()
                models_to_clear += [('Channel', Channel.objects.filter(tenant=tenant))]
            except Exception:
                pass
            try:
                from compliance.models import IncidentReport, RAMSDocument
                models_to_clear += [
                    ('IncidentReport', IncidentReport.objects.filter(tenant=tenant)),
                    ('RAMSDocument', RAMSDocument.objects.filter(tenant=tenant)),
                ]
            except Exception:
                pass
            try:
                from documents.models import DocumentTag
                models_to_clear += [('DocumentTag', DocumentTag.objects.filter(tenant=tenant))]
            except Exception:
                pass
            try:
                from crm.models import Lead
                models_to_clear += [('Lead', Lead.objects.filter(tenant=tenant))]
            except Exception:
                pass

            for name, qs in models_to_clear:
                count = qs.count()
                if count:
                    qs.delete()
                    self.stdout.write(f'  Deleted {count} {name}')

            # Delete demo users (prefixed with tenant slug)
            demo_users = User.objects.filter(username__startswith=f'{slug}-', tenant=tenant)
            u_count = demo_users.count()
            if u_count:
                demo_users.delete()
                self.stdout.write(f'  Deleted {u_count} demo users')

            self.stdout.write(self.style.SUCCESS(f'  Done — {slug} demo data cleared'))

    def _user(self, username, email, first, last, role):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email, 'first_name': first, 'last_name': last,
                'role': role, 'is_staff': role in ('owner', 'manager'),
                'is_superuser': role == 'owner',
                'tenant': self.tenant,
            }
        )
        if created:
            user.set_password('admin123')
            user.save()
        else:
            # Ensure demo users are always active and linked to correct tenant on re-seed
            changed = False
            if not user.is_active:
                user.is_active = True
                changed = True
            if user.role != role:
                user.role = role
                user.is_staff = role in ('owner', 'manager')
                user.is_superuser = role == 'owner'
                changed = True
            if user.tenant != self.tenant:
                user.tenant = self.tenant
                changed = True
            if changed:
                user.save()
        return user

    def _seed_tenant(self, slug, cfg):
        from tenants.models import TenantSettings
        defaults = {
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
        for key in ('business_type', 'colour_background', 'colour_text', 'font_heading', 'font_body',
                    'font_url', 'website_url', 'social_instagram',
                    'booking_staff_label', 'booking_staff_label_plural'):
            if key in cfg:
                defaults[key] = cfg[key]
        ts, created = TenantSettings.objects.update_or_create(slug=slug, defaults=defaults)
        self.stdout.write(f'  Tenant: {ts.business_name} ({"created" if created else "updated"})')
        return ts

    def _seed_bookings(self, cfg, customer):
        import random
        import hashlib
        from bookings.models import Service, Staff as BookingStaff, Client, Booking

        # --- Services ---
        for name, cat, dur, price, dep in cfg['services']:
            Service.objects.get_or_create(
                tenant=self.tenant, name=name,
                defaults={
                    'category': cat,
                    'duration_minutes': dur,
                    'price': Decimal(price),
                    'deposit_pence': dep,
                    'payment_type': 'deposit' if dep > 0 else ('free' if Decimal(price) == 0 else 'full'),
                }
            )
        svc_count = Service.objects.filter(tenant=self.tenant).count()
        self.stdout.write(f'  Services: {svc_count}')

        # --- Booking Staff ---
        staff_configs = cfg.get('booking_staff', [
            (f'staff1@{self.tenant.slug}.demo', 'Staff Member', 'staff', []),
        ])
        all_services = list(Service.objects.filter(tenant=self.tenant))
        svc_by_name = {s.name: s for s in all_services}
        booking_staff = []
        from datetime import time as dt_time
        for entry in staff_configs:
            s_email, s_name, s_role = entry[0], entry[1], entry[2]
            svc_names = entry[3] if len(entry) > 3 else []
            break_start_str = entry[4] if len(entry) > 4 else None
            break_end_str = entry[5] if len(entry) > 5 else None
            defaults = {'name': s_name, 'role': s_role}
            if break_start_str:
                h, m = map(int, break_start_str.split(':'))
                defaults['break_start'] = dt_time(h, m)
            if break_end_str:
                h, m = map(int, break_end_str.split(':'))
                defaults['break_end'] = dt_time(h, m)
            bs, created = BookingStaff.objects.get_or_create(
                tenant=self.tenant, email=s_email,
                defaults=defaults
            )
            if not created:
                changed = False
                if bs.name != s_name:
                    bs.name = s_name
                    changed = True
                if break_start_str:
                    h, m = map(int, break_start_str.split(':'))
                    if bs.break_start != dt_time(h, m):
                        bs.break_start = dt_time(h, m)
                        changed = True
                if break_end_str:
                    h, m = map(int, break_end_str.split(':'))
                    if bs.break_end != dt_time(h, m):
                        bs.break_end = dt_time(h, m)
                        changed = True
                if changed:
                    bs.save()
            if svc_names:
                bs.services.set([svc_by_name[n] for n in svc_names if n in svc_by_name])
            else:
                bs.services.set(all_services)
            booking_staff.append(bs)
        BookingStaff.objects.filter(tenant=self.tenant, email=f'staff@{self.tenant.slug}.demo').exclude(
            id__in=[s.id for s in booking_staff]
        ).delete()
        self.stdout.write(f'  Booking staff: {len(booking_staff)}')

        # --- Demo Clients ---
        demo_clients = []
        # Always include the default customer user
        default_client, _ = Client.objects.get_or_create(
            tenant=self.tenant, email=customer.email,
            defaults={'name': customer.get_full_name(), 'phone': '07700 900001'}
        )
        demo_clients.append(default_client)
        # Create additional named demo clients from config
        for c_name, c_email, c_phone in cfg.get('demo_clients', []):
            cl, _ = Client.objects.get_or_create(
                tenant=self.tenant, email=c_email,
                defaults={'name': c_name, 'phone': c_phone}
            )
            demo_clients.append(cl)
        self.stdout.write(f'  Clients: {len(demo_clients)}')

        # --- Historic + Future Bookings (90 days back, 14 days forward) ---
        if Booking.objects.filter(tenant=self.tenant).count() >= 50:
            bk_count = Booking.objects.filter(tenant=self.tenant).count()
            self.stdout.write(f'  Bookings: {bk_count} (already seeded)')
            return

        # Deterministic seed per tenant for reproducible data
        rng = random.Random(hashlib.md5(self.tenant.slug.encode()).hexdigest())

        # Build staff→services mapping for realistic assignment
        staff_svc_map = {}
        for bs in booking_staff:
            staff_svc_map[bs.id] = list(bs.services.all())
            if not staff_svc_map[bs.id]:
                staff_svc_map[bs.id] = all_services

        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        bookings_to_create = []
        HOURS = [9, 10, 11, 13, 14, 15, 16, 17, 18, 19]  # bookable hours

        for day_offset in range(-90, 15):
            day = today_start + timedelta(days=day_offset)
            if day.weekday() == 6:  # skip Sundays
                continue
            # Vary bookings per day: weekdays busier, weekends moderate
            if day.weekday() == 5:  # Saturday
                n_bookings = rng.randint(3, 6)
            elif day.weekday() == 4:  # Friday
                n_bookings = rng.randint(4, 8)
            else:
                n_bookings = rng.randint(2, 6)

            for _ in range(n_bookings):
                staff_member = rng.choice(booking_staff)
                available_svcs = staff_svc_map.get(staff_member.id, all_services)
                if not available_svcs:
                    continue
                svc = rng.choice(available_svcs)
                client = rng.choice(demo_clients)
                hour = rng.choice(HOURS)
                minute = rng.choice([0, 15, 30, 45])
                start = day.replace(hour=hour, minute=minute)
                end = start + timedelta(minutes=svc.duration_minutes)

                # Status distribution: past bookings mostly completed
                if day_offset < -7:
                    status = rng.choices(
                        ['completed', 'cancelled', 'no_show'],
                        weights=[80, 12, 8]
                    )[0]
                elif day_offset < 0:
                    status = rng.choices(
                        ['completed', 'confirmed', 'cancelled', 'no_show'],
                        weights=[60, 20, 12, 8]
                    )[0]
                elif day_offset == 0:
                    status = rng.choices(
                        ['confirmed', 'pending', 'completed'],
                        weights=[50, 30, 20]
                    )[0]
                else:
                    status = rng.choices(
                        ['confirmed', 'pending'],
                        weights=[70, 30]
                    )[0]

                bookings_to_create.append(Booking(
                    tenant=self.tenant,
                    client=client,
                    service=svc,
                    staff=staff_member,
                    start_time=start,
                    end_time=end,
                    status=status,
                    payment_amount=svc.price if status == 'completed' else None,
                    payment_status='paid' if status == 'completed' else 'pending',
                ))

        # Bulk create for speed
        if bookings_to_create:
            Booking.objects.bulk_create(bookings_to_create, ignore_conflicts=True)
        bk_count = Booking.objects.filter(tenant=self.tenant).count()
        self.stdout.write(f'  Bookings: {bk_count} ({len(bookings_to_create)} generated)')

    def _seed_staff(self, cfg, owner, manager, staff1, staff2):
        from staff.models import StaffProfile, Shift, LeaveRequest, TrainingRecord, WorkingHours, ProjectCode, TimesheetEntry

        location = cfg['business_name']
        profiles = {}
        for user, name in [(owner, 'Jordan Riley'), (manager, 'Alex Morgan'), (staff1, 'Sam Kim'), (staff2, 'Taylor Chen')]:
            p, _ = StaffProfile.objects.get_or_create(
                user=user, defaults={'tenant': self.tenant, 'display_name': name, 'phone': user.email}
            )
            if not p.tenant:
                p.tenant = self.tenant
                p.save(update_fields=['tenant'])
            profiles[user.username] = p

        today = date.today()
        for p in profiles.values():
            for day_offset in range(5):
                d = today + timedelta(days=day_offset)
                Shift.objects.get_or_create(
                    staff=p, date=d, start_time=time(9, 0),
                    defaults={'end_time': time(17, 0), 'location': location, 'is_published': True}
                )

        staff1_key = f'{self.tenant.slug}-staff1'
        staff2_key = f'{self.tenant.slug}-staff2'
        manager_key = f'{self.tenant.slug}-manager'
        if staff1_key in profiles:
            LeaveRequest.objects.get_or_create(
                staff=profiles[staff1_key], start_date=today + timedelta(days=10),
                defaults={'end_date': today + timedelta(days=12), 'leave_type': 'ANNUAL', 'reason': 'Holiday', 'status': 'PENDING'}
            )
            TrainingRecord.objects.get_or_create(
                staff=profiles[staff1_key], title='Fire Safety',
                defaults={'provider': 'SafetyFirst Ltd', 'completed_date': today - timedelta(days=60), 'expiry_date': today + timedelta(days=300)}
            )
        if staff2_key in profiles:
            LeaveRequest.objects.get_or_create(
                staff=profiles[staff2_key], start_date=today + timedelta(days=20),
                defaults={'end_date': today + timedelta(days=21), 'leave_type': 'SICK', 'reason': 'Medical appointment', 'status': 'APPROVED',
                          'reviewed_by': profiles.get(manager_key)}
            )
            TrainingRecord.objects.get_or_create(
                staff=profiles[staff2_key], title='COSHH Awareness',
                defaults={'provider': 'HSE Online', 'completed_date': today - timedelta(days=400), 'expiry_date': today - timedelta(days=35)}
            )

        # --- Working Hours (Mon-Fri 9-17 for all, Sat 10-14 for staff) ---
        for p in profiles.values():
            for day in range(5):  # Mon-Fri
                WorkingHours.objects.get_or_create(
                    staff=p, day_of_week=day,
                    defaults={'start_time': time(9, 0), 'end_time': time(17, 0), 'break_minutes': 30, 'is_active': True}
                )
        # Staff1 also works Saturday mornings
        if staff1_key in profiles:
            WorkingHours.objects.get_or_create(
                staff=profiles[staff1_key], day_of_week=5,
                defaults={'start_time': time(10, 0), 'end_time': time(14, 0), 'break_minutes': 0, 'is_active': True}
            )
        wh_count = WorkingHours.objects.filter(staff__tenant=self.tenant).count()
        self.stdout.write(f'  Working hours: {wh_count}')

        # --- Project Codes ---
        pc1, _ = ProjectCode.objects.get_or_create(
            tenant=self.tenant, code='GEN',
            defaults={'name': 'General Operations', 'is_billable': False}
        )
        pc2, _ = ProjectCode.objects.get_or_create(
            tenant=self.tenant, code='CLIENT-A',
            defaults={'name': 'Client A Project', 'client_name': 'Client A Ltd', 'is_billable': True, 'hourly_rate': Decimal('45.00')}
        )
        pc_count = ProjectCode.objects.filter(tenant=self.tenant).count()
        self.stdout.write(f'  Project codes: {pc_count}')

        # --- Timesheets (last 7 working days for all staff) ---
        ts_count_before = TimesheetEntry.objects.filter(staff__tenant=self.tenant).count()
        if ts_count_before == 0:
            for p in profiles.values():
                for day_offset in range(-7, 0):
                    d = today + timedelta(days=day_offset)
                    if d.weekday() >= 5:
                        continue  # skip weekends
                    pc = pc2 if day_offset % 3 == 0 else pc1
                    # Slight variance for realism
                    actual_start = time(9, 0) if day_offset % 4 != 0 else time(9, 15)
                    actual_end = time(17, 0) if day_offset % 5 != 0 else time(16, 45)
                    status = 'WORKED' if day_offset % 7 != -1 else 'LATE'
                    TimesheetEntry.objects.get_or_create(
                        staff=p, date=d,
                        defaults={
                            'scheduled_start': time(9, 0), 'scheduled_end': time(17, 0),
                            'scheduled_break_minutes': 30,
                            'actual_start': actual_start, 'actual_end': actual_end,
                            'actual_break_minutes': 30,
                            'status': status,
                            'project_code': pc,
                        }
                    )
        ts_count = TimesheetEntry.objects.filter(staff__tenant=self.tenant).count()
        self.stdout.write(f'  Timesheet entries: {ts_count}')

        sp_count = StaffProfile.objects.filter(tenant=self.tenant).count()
        self.stdout.write(f'  Staff profiles: {sp_count}')

    def _seed_staff_custom(self, cfg):
        """Seed staff profiles for tenants with custom staff_users config."""
        from staff.models import StaffProfile, WorkingHours
        for uname, uemail, ufirst, ulast, urole in cfg['staff_users']:
            try:
                user = User.objects.get(username=uname)
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  User {uname} not found — skipping StaffProfile'))
                continue
            p, created = StaffProfile.objects.get_or_create(
                user=user,
                defaults={'tenant': self.tenant, 'display_name': f'{ufirst} {ulast}', 'phone': cfg.get('phone', '')}
            )
            # Always ensure correct tenant and display name
            changed = False
            if p.tenant != self.tenant:
                p.tenant = self.tenant
                changed = True
            if p.display_name != f'{ufirst} {ulast}':
                p.display_name = f'{ufirst} {ulast}'
                changed = True
            if not p.is_active:
                p.is_active = True
                changed = True
            if changed:
                p.save()
            for day in range(5):
                WorkingHours.objects.get_or_create(
                    staff=p, day_of_week=day,
                    defaults={'start_time': time(9, 0), 'end_time': time(17, 0), 'is_active': True}
                )
            self.stdout.write(f'  StaffProfile: {ufirst} {ulast} ({"created" if created else "exists"})')
        sp_count = StaffProfile.objects.filter(tenant=self.tenant).count()
        self.stdout.write(f'  Custom staff profiles: {sp_count}')

    def _seed_disclaimer(self, dcfg):
        """Seed a disclaimer using the IntakeWellbeingDisclaimer model."""
        from bookings.models_intake import IntakeWellbeingDisclaimer
        version = str(dcfg.get('version', '1.0'))
        dt, created = IntakeWellbeingDisclaimer.objects.get_or_create(
            version=version,
            defaults={
                'content': dcfg['body'],
                'active': True,
            }
        )
        self.stdout.write(f'  Disclaimer: v{dt.version} ({"created" if created else "exists"})')

    def _seed_comms(self, slug, cfg, owner, manager, staff1, staff2):
        try:
            from comms.models import Channel, ChannelMember, Message
        except Exception:
            self.stdout.write('  Comms module not available — skipping')
            return

        channels = []
        for ch_name, ch_type in cfg['comms_channels']:
            ch, _ = Channel.objects.get_or_create(tenant=self.tenant, name=ch_name, defaults={'channel_type': ch_type})
            if slug != 'nbne':
                for u in [owner, manager, staff1, staff2]:
                    ChannelMember.objects.get_or_create(channel=ch, user=u)
            channels.append(ch)

        if slug != 'nbne' and channels and not Message.objects.filter(channel=channels[0]).exists():
            Message.objects.create(channel=channels[0], sender=owner, body='Welcome to the team chat!')
            Message.objects.create(channel=channels[0], sender=staff1, body='Thanks! Excited to be here.')
            Message.objects.create(channel=channels[0], sender=manager, body='Remember to check the rota for next week.')
        ch_count = Channel.objects.filter(tenant=self.tenant).count()
        self.stdout.write(f'  Channels: {ch_count}')

    def _seed_compliance(self, owner, staff1):
        from compliance.models import (
            IncidentReport, RAMSDocument, ComplianceCategory, ComplianceItem, PeaceOfMindScore,
        )

        # --- Seed UK baseline compliance items per tenant ---
        from compliance.management.commands.seed_compliance import UK_BASELINE

        # Disconnect signals during bulk seed to avoid N recalculations
        from django.db.models.signals import post_save, post_delete
        from compliance.signals import recalculate_score_on_save, recalculate_score_on_delete
        post_save.disconnect(recalculate_score_on_save)
        post_delete.disconnect(recalculate_score_on_delete)

        today = date.today()
        item_count = 0
        # Vary due dates for realistic demo: some overdue, some due soon, some compliant
        due_offsets = [-15, -5, 10, 25, 45, 90, 120, 180, 200, 250, 300, 330, 14, 60, 7, 21, 35, 150, 270, 365]
        idx = 0
        for cat_data in UK_BASELINE:
            cat, _ = ComplianceCategory.objects.get_or_create(
                tenant=self.tenant, name=cat_data['category'],
                defaults={'max_score': 10}
            )
            for item_data in cat_data['items']:
                offset = due_offsets[idx % len(due_offsets)]
                idx += 1
                due = today + timedelta(days=offset)
                obj, created = ComplianceItem.objects.get_or_create(
                    title=item_data['title'], category=cat,
                    defaults={
                        'description': item_data['description'],
                        'item_type': item_data['item_type'],
                        'frequency_type': item_data['frequency_type'],
                        'evidence_required': item_data['evidence_required'],
                        'regulatory_ref': item_data['regulatory_ref'],
                        'legal_reference': item_data['legal_reference'],
                        'plain_english_why': item_data.get('plain_english_why', ''),
                        'primary_action': item_data.get('primary_action', ''),
                        'next_due_date': due,
                        'due_date': due,
                    }
                )
                if not created:
                    obj.plain_english_why = item_data.get('plain_english_why', '')
                    obj.primary_action = item_data.get('primary_action', '')
                    obj.description = item_data['description']
                    obj.legal_reference = item_data['legal_reference']
                    obj.save(update_fields=['plain_english_why', 'primary_action', 'description', 'legal_reference'])
                else:
                    item_count += 1
        self.stdout.write(f'  Compliance items: {item_count} new, {ComplianceItem.objects.filter(category__tenant=self.tenant).count()} total')

        # Reconnect signals
        post_save.connect(recalculate_score_on_save)
        post_delete.connect(recalculate_score_on_delete)

        # Recalculate score for this tenant
        PeaceOfMindScore.recalculate(tenant=self.tenant)

        # --- Seed incidents ---
        IncidentReport.objects.get_or_create(
            tenant=self.tenant, title='Wet floor slip hazard',
            defaults={
                'description': 'Water pooling near wash stations during busy period.',
                'severity': 'MEDIUM', 'status': 'INVESTIGATING', 'location': 'Wash Area',
                'incident_date': timezone.now() - timedelta(days=3), 'reported_by': staff1,
            }
        )
        IncidentReport.objects.get_or_create(
            tenant=self.tenant, title='Chemical storage unlabelled',
            defaults={
                'description': 'Several COSHH substances found without proper labels.',
                'severity': 'HIGH', 'status': 'OPEN', 'location': 'Store Room',
                'incident_date': timezone.now() - timedelta(days=1), 'reported_by': staff1,
            }
        )
        RAMSDocument.objects.get_or_create(
            tenant=self.tenant, title='General Risk Assessment',
            defaults={
                'reference_number': 'RAMS-001', 'description': 'General risk assessment for operations.',
                'status': 'ACTIVE', 'issue_date': date.today() - timedelta(days=90),
                'expiry_date': date.today() + timedelta(days=275), 'created_by': owner,
            }
        )
        inc_count = IncidentReport.objects.filter(tenant=self.tenant).count()
        self.stdout.write(f'  Incidents: {inc_count}')

    def _seed_documents(self, owner, manager):
        from documents.models import DocumentTag

        for tag_name in ['Policy', 'HSE', 'Training', 'HR']:
            DocumentTag.objects.get_or_create(tenant=self.tenant, name=tag_name)
        tag_count = DocumentTag.objects.filter(tenant=self.tenant).count()
        self.stdout.write(f'  Document tags: {tag_count}')

    def _seed_crm(self, owner, manager):
        from crm.models import Lead, LeadNote, LeadHistory

        today = date.today()
        leads_data = [
            {'name': 'Emma Wilson', 'email': 'emma@example.com', 'phone': '07700 900123', 'source': 'website', 'status': 'CONVERTED', 'value_pence': 15000, 'marketing_consent': True, 'notes': 'Regular client, books monthly.', 'last_contact_date': today - timedelta(days=3)},
            {'name': 'Liam Brown', 'email': 'liam@example.com', 'phone': '07700 900456', 'source': 'referral', 'status': 'QUALIFIED', 'value_pence': 8000, 'marketing_consent': True, 'notes': 'Referred by Emma. Interested in premium package.', 'follow_up_date': today + timedelta(days=2)},
            {'name': 'Sophia Davis', 'email': 'sophia@example.com', 'phone': '07700 900789', 'source': 'social', 'status': 'NEW', 'value_pence': 5000, 'marketing_consent': False, 'notes': 'Enquired via Instagram DM.'},
            {'name': 'Noah Taylor', 'email': 'noah@example.com', 'phone': '07700 900321', 'source': 'manual', 'status': 'CONTACTED', 'value_pence': 12000, 'marketing_consent': True, 'notes': 'Called, asked to ring back next week.', 'follow_up_date': today - timedelta(days=3), 'last_contact_date': today - timedelta(days=10)},
            {'name': 'Olivia Jones', 'email': 'olivia@example.com', 'phone': '07700 900654', 'source': 'other', 'status': 'LOST', 'value_pence': 3000, 'marketing_consent': False, 'notes': 'Went with competitor.'},
            {'name': 'James Anderson', 'email': 'james.a@example.com', 'phone': '07700 900111', 'source': 'website', 'status': 'NEW', 'value_pence': 7500, 'marketing_consent': True, 'notes': 'Filled in contact form yesterday.'},
            {'name': 'Charlotte Hughes', 'email': 'charlotte.h@example.com', 'phone': '07700 900222', 'source': 'referral', 'status': 'CONTACTED', 'value_pence': 20000, 'marketing_consent': True, 'notes': 'Wedding party booking enquiry. High value.', 'follow_up_date': today, 'last_contact_date': today - timedelta(days=5)},
            {'name': 'Harry Clarke', 'email': 'harry.c@example.com', 'phone': '', 'source': 'social', 'status': 'CONTACTED', 'value_pence': 4000, 'marketing_consent': False, 'notes': 'Messaged on Facebook.', 'follow_up_date': today - timedelta(days=8), 'last_contact_date': today - timedelta(days=15)},
        ]
        for ld in leads_data:
            lead, created = Lead.objects.get_or_create(
                tenant=self.tenant, email=ld['email'],
                defaults={
                    'name': ld['name'], 'phone': ld.get('phone', ''), 'source': ld['source'],
                    'status': ld['status'], 'value_pence': ld['value_pence'],
                    'marketing_consent': ld.get('marketing_consent', False),
                    'notes': ld.get('notes', ''),
                    'follow_up_date': ld.get('follow_up_date'),
                    'last_contact_date': ld.get('last_contact_date'),
                }
            )
            if created:
                LeadHistory.objects.get_or_create(lead=lead, action='Lead created', defaults={'detail': f'Source: {ld["source"]}'})
                if ld['status'] == 'CONTACTED':
                    LeadHistory.objects.get_or_create(lead=lead, action='Contacted', defaults={'detail': 'Initial contact made'})
                if ld['status'] == 'QUALIFIED':
                    LeadHistory.objects.get_or_create(lead=lead, action='Qualified', defaults={'detail': 'Moved to qualified'})
                if ld['status'] == 'CONVERTED':
                    LeadHistory.objects.get_or_create(lead=lead, action='Converted to client', defaults={'detail': ''})
                if ld.get('notes'):
                    LeadNote.objects.get_or_create(lead=lead, text=ld['notes'], defaults={'created_by': 'System'})

        lead_count = Lead.objects.filter(tenant=self.tenant).count()
        self.stdout.write(f'  Leads: {lead_count}')
