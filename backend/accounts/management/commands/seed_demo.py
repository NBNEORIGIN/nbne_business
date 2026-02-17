"""Management command to seed 3 exemplar demo tenants: Salon X, Restaurant X, Health Club X."""
from datetime import date, time, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


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
            ('Cut & Style', 'Cuts', 45, '35.00', 1000),
            ('Colour Full', 'Colour', 120, '95.00', 2500),
            ('Balayage', 'Colour', 150, '140.00', 4000),
            ('Blow Dry', 'Styling', 30, '25.00', 0),
            ('Bridal Package', 'Special', 180, '250.00', 7500),
            ('Gents Cut', 'Cuts', 30, '20.00', 0),
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
            ('Table for 2', 'Dining', 90, '0.00', 0),
            ('Table for 4', 'Dining', 120, '0.00', 0),
            ('Private Dining Room', 'Events', 180, '500.00', 10000),
            ('Afternoon Tea', 'Experiences', 120, '45.00', 1500),
            ('Chef\'s Table', 'Experiences', 150, '120.00', 5000),
            ('Corporate Event', 'Events', 240, '2000.00', 50000),
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
            ('Personal Training', 'Training', 60, '50.00', 1500),
            ('Group Class', 'Classes', 45, '12.00', 0),
            ('Sports Massage', 'Wellness', 60, '55.00', 1500),
            ('Swimming Lane', 'Facilities', 60, '8.00', 0),
            ('Sauna & Steam', 'Wellness', 90, '15.00', 0),
            ('Physiotherapy', 'Medical', 45, '75.00', 2000),
        ],
        'comms_channels': [('General', 'GENERAL'), ('Trainers', 'TEAM'), ('Front Desk', 'TEAM')],
    },
    'mind-department': {
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
        for key in ('colour_background', 'colour_text', 'font_heading', 'font_body',
                    'font_url', 'website_url', 'social_instagram'):
            if key in cfg:
                defaults[key] = cfg[key]
        ts, created = TenantSettings.objects.update_or_create(slug=slug, defaults=defaults)
        self.stdout.write(f'  Tenant: {ts.business_name} ({"created" if created else "updated"})')
        return ts

    def _seed_bookings(self, cfg, customer):
        from bookings.models import Service, Staff as BookingStaff, Client, Booking

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

        demo_staff, _ = BookingStaff.objects.get_or_create(
            tenant=self.tenant, email=f'staff@{self.tenant.slug}.demo',
            defaults={'name': 'Demo Staff', 'role': 'staff'}
        )
        demo_staff.services.set(Service.objects.filter(tenant=self.tenant))

        demo_client, _ = Client.objects.get_or_create(
            tenant=self.tenant, email=customer.email,
            defaults={'name': customer.get_full_name(), 'phone': '07700 900001'}
        )

        if not Booking.objects.filter(tenant=self.tenant).exists():
            svc = Service.objects.filter(tenant=self.tenant).first()
            if svc:
                today = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
                statuses = ['confirmed', 'pending', 'completed', 'cancelled', 'confirmed']
                for i, st in enumerate(statuses):
                    start = today + timedelta(days=i + 1)
                    end = start + timedelta(minutes=svc.duration_minutes)
                    Booking.objects.create(
                        tenant=self.tenant,
                        client=demo_client,
                        service=svc,
                        staff=demo_staff,
                        start_time=start,
                        end_time=end,
                        status=st,
                    )
        bk_count = Booking.objects.filter(tenant=self.tenant).count()
        self.stdout.write(f'  Bookings: {bk_count}')

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
            user = User.objects.get(username=uname)
            p, _ = StaffProfile.objects.get_or_create(
                user=user,
                defaults={'tenant': self.tenant, 'display_name': f'{ufirst} {ulast}', 'phone': cfg.get('phone', '')}
            )
            if not p.tenant:
                p.tenant = self.tenant
                p.save(update_fields=['tenant'])
            for day in range(5):
                WorkingHours.objects.get_or_create(
                    staff=p, day_of_week=day,
                    defaults={'start_time': time(9, 0), 'end_time': time(17, 0), 'is_active': True}
                )
        self.stdout.write(f'  Custom staff profiles seeded')

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
        from compliance.models import IncidentReport, RAMSDocument

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
        from crm.models import Lead

        leads_data = [
            ('Emma Wilson', 'emma@example.com', 'website', 'CONVERTED', 15000),
            ('Liam Brown', 'liam@example.com', 'referral', 'QUALIFIED', 8000),
            ('Sophia Davis', 'sophia@example.com', 'social', 'NEW', 5000),
            ('Noah Taylor', 'noah@example.com', 'manual', 'CONTACTED', 12000),
            ('Olivia Jones', 'olivia@example.com', 'other', 'LOST', 3000),
        ]
        for name, email, source, status, value in leads_data:
            Lead.objects.get_or_create(
                tenant=self.tenant, email=email,
                defaults={'name': name, 'source': source, 'status': status, 'value_pence': value}
            )
        lead_count = Lead.objects.filter(tenant=self.tenant).count()
        self.stdout.write(f'  Leads: {lead_count}')
