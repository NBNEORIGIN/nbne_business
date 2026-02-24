"""
Management command to provision a new production tenant.
Unlike seed_demo, this creates a REAL tenant with persistent data
and a proper owner account (no nightly reset).

Usage:
    python manage.py provision_tenant \
        --slug my-salon \
        --name "My Salon" \
        --type salon \
        --email hello@mysalon.co.uk \
        --owner-email sarah@mysalon.co.uk \
        --owner-first Sarah \
        --owner-last Thompson

    Optional flags:
        --modules bookings,payments,staff,crm,compliance,documents,comms
        --phone "07700 123456"
        --address "123 High Street, London"
        --colour "#8B6F47"
"""
import secrets
import string

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

DEFAULT_MODULES = ['bookings', 'payments', 'staff', 'crm', 'compliance', 'documents', 'comms']

VALID_TYPES = ['salon', 'restaurant', 'gym', 'generic']


def generate_password(length=12):
    chars = string.ascii_letters + string.digits + '!@#$%'
    return ''.join(secrets.choice(chars) for _ in range(length))


class Command(BaseCommand):
    help = 'Provision a new production tenant with owner account'

    def add_arguments(self, parser):
        parser.add_argument('--slug', required=True, help='Tenant slug (e.g. my-salon)')
        parser.add_argument('--name', required=True, help='Business name (e.g. My Salon)')
        parser.add_argument('--type', required=True, choices=VALID_TYPES, help='Business type')
        parser.add_argument('--email', required=True, help='Business contact email')
        parser.add_argument('--owner-email', required=True, help='Owner login email')
        parser.add_argument('--owner-first', required=True, help='Owner first name')
        parser.add_argument('--owner-last', required=True, help='Owner last name')
        parser.add_argument('--phone', default='', help='Business phone')
        parser.add_argument('--address', default='', help='Business address')
        parser.add_argument('--colour', default='#2563eb', help='Primary brand colour')
        parser.add_argument('--modules', default=','.join(DEFAULT_MODULES),
                            help='Comma-separated enabled modules')
        parser.add_argument('--owner-password', default='',
                            help='Owner password (auto-generated if not set)')
        parser.add_argument('--dry-run', action='store_true',
                            help='Show what would be created without writing to DB')

    @transaction.atomic
    def handle(self, *args, **options):
        from tenants.models import TenantSettings

        slug = options['slug'].strip().lower()
        name = options['name'].strip()
        btype = options['type']
        email = options['email'].strip()
        owner_email = options['owner_email'].strip()
        owner_first = options['owner_first'].strip()
        owner_last = options['owner_last'].strip()
        phone = options['phone'].strip()
        address = options['address'].strip()
        colour = options['colour'].strip()
        modules = [m.strip() for m in options['modules'].split(',') if m.strip()]
        password = options['owner_password'] or generate_password()
        dry_run = options['dry_run']

        # Validate slug
        import re
        if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', slug):
            raise CommandError('Slug must be lowercase alphanumeric with hyphens only.')

        # Check for existing tenant
        if TenantSettings.objects.filter(slug=slug).exists():
            raise CommandError(f'Tenant with slug "{slug}" already exists.')

        # Check for existing user
        if User.objects.filter(email=owner_email).exists():
            raise CommandError(f'User with email "{owner_email}" already exists.')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n  DRY RUN — nothing will be created\n'))

        self.stdout.write(f'\n  Tenant:  {name} ({slug})')
        self.stdout.write(f'  Type:    {btype}')
        self.stdout.write(f'  Email:   {email}')
        self.stdout.write(f'  Phone:   {phone or "—"}')
        self.stdout.write(f'  Address: {address or "—"}')
        self.stdout.write(f'  Colour:  {colour}')
        self.stdout.write(f'  Modules: {", ".join(modules)}')
        self.stdout.write(f'  Owner:   {owner_first} {owner_last} ({owner_email})')
        self.stdout.write(f'  Password: {password}')
        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.SUCCESS('  Dry run complete. Use without --dry-run to create.'))
            return

        # Create tenant
        tenant = TenantSettings.objects.create(
            slug=slug,
            business_name=name,
            business_type=btype,
            email=email,
            phone=phone,
            address=address,
            colour_primary=colour,
            colour_secondary=colour,
            enabled_modules=modules,
        )
        self.stdout.write(self.style.SUCCESS(f'  Created tenant: {tenant}'))

        # Create owner user
        owner = User.objects.create_user(
            username=f'{slug}-owner',
            email=owner_email,
            password=password,
            first_name=owner_first,
            last_name=owner_last,
            role='owner',
        )
        self.stdout.write(self.style.SUCCESS(f'  Created owner: {owner.email}'))

        # Link owner to tenant
        owner.tenant = tenant
        owner.save(update_fields=['tenant'])

        # Create StaffProfile for owner
        if 'staff' in modules:
            try:
                from staff.models import StaffProfile
                StaffProfile.objects.create(
                    user=owner,
                    tenant=tenant,
                    display_name=f'{owner_first} {owner_last}',
                    role='owner',
                    is_active=True,
                )
                self.stdout.write(self.style.SUCCESS(f'  Created staff profile for owner'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Could not create staff profile: {e}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('  ═══════════════════════════════════════'))
        self.stdout.write(self.style.SUCCESS(f'  Tenant "{name}" provisioned successfully!'))
        self.stdout.write(self.style.SUCCESS('  ═══════════════════════════════════════'))
        self.stdout.write('')
        self.stdout.write(f'  Login credentials:')
        self.stdout.write(f'    Email:    {owner_email}')
        self.stdout.write(f'    Password: {password}')
        self.stdout.write('')
        self.stdout.write(f'  Next steps:')
        self.stdout.write(f'    1. Create a Vercel project with NEXT_PUBLIC_TENANT_SLUG={slug}')
        self.stdout.write(f'    2. Set DJANGO_BACKEND_URL to point to the correct Railway backend')
        self.stdout.write(f'    3. Share login credentials with the client')
        self.stdout.write(f'    4. Add services, staff, and branding via the admin panel')
        self.stdout.write('')
