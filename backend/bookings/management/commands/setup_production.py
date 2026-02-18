from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from bookings.models import Service, Staff, IntakeWellbeingDisclaimer, ClassPackage
from decimal import Decimal


class Command(BaseCommand):
    help = 'Setup production data: demo users, default service, disclaimer, and package'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        # Create superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@demo.local', 'admin123')
            self.stdout.write(self.style.SUCCESS('✓ Superuser created: admin'))
        else:
            self.stdout.write('✓ Superuser already exists')

        # Create demo users matching frontend login page
        if not User.objects.filter(username='owner').exists():
            User.objects.create_superuser('owner', 'owner@demo.local', 'admin123')
            self.stdout.write(self.style.SUCCESS('✓ Demo owner created'))
        if not User.objects.filter(username='manager').exists():
            u = User.objects.create_user('manager', 'manager@demo.local', 'admin123')
            u.is_staff = True
            u.save()
            self.stdout.write(self.style.SUCCESS('✓ Demo manager created'))
        if not User.objects.filter(username='staff1').exists():
            User.objects.create_user('staff1', 'staff1@demo.local', 'admin123')
            self.stdout.write(self.style.SUCCESS('✓ Demo staff1 created'))

        # Create default Service (requires tenant)
        from tenants.models import TenantSettings
        default_tenant = TenantSettings.objects.first()
        if default_tenant:
            service, created = Service.objects.get_or_create(
                name='Consultation', tenant=default_tenant,
                defaults={
                    'description': '60-minute consultation session',
                    'duration_minutes': 60,
                    'price': Decimal('50.00'),
                    'active': True
                }
            )
        else:
            created = False
            service = None
        if service:
            self.stdout.write(self.style.SUCCESS(f'✓ {"Created" if created else "Found"} service: {service.name}'))
        else:
            self.stdout.write('⚠ No tenant found — skipped default service creation')

        # Staff members should be created manually via admin interface
        self.stdout.write(self.style.SUCCESS('✓ Staff members managed via admin interface'))

        # Create default Disclaimer
        disclaimer_content = """<h2>Health & Wellness Consent and Liability Waiver</h2>

<h3>Introduction</h3>
<p>Welcome. Our services are designed to support your wellbeing. Please read the following terms carefully before proceeding.</p>

<h3>Not Medical Advice</h3>
<p>I understand that the services provided are not a substitute for professional medical advice, diagnosis, or treatment. I agree that I should not discontinue or avoid any medical treatment recommended by my physician or other licensed healthcare provider.</p>

<h3>Assumption of Risk</h3>
<p>I understand that participating in services may involve physical exertion or other activities that carry inherent risks. I voluntarily assume full responsibility for any risks, injuries, or damages, known or unknown, which I might incur as a result of participating in the services.</p>

<h3>Health Conditions</h3>
<p>I confirm that I am in good medical condition and sufficiently fit to participate. It is my responsibility to inform the provider immediately of any pre-existing conditions that may be affected by the services.</p>

<h3>Release of Liability</h3>
<p>I hereby waive and release the service provider, its employees, agents, and representatives from any and all claims, demands, or causes of action for injuries, damages, or losses that I may incur arising from my participation in the services, to the fullest extent permitted by law.</p>

<h3>Confidentiality</h3>
<p>All personal information and records will be kept confidential, unless consent is given in writing to share this information or if disclosure is required by law.</p>

<h3>Cancellation Policy</h3>
<p>A 24-hour notice is required to cancel or reschedule appointments. Failure to do so may result in a charge for the full cost of the session.</p>

<h3>Acknowledgment</h3>
<p>I have read and fully understand the above statements. By completing this intake form and checking the consent boxes below, I am acknowledging that I understand and agree to these terms.</p>"""

        disclaimer, created = IntakeWellbeingDisclaimer.objects.get_or_create(
            version='1.0',
            defaults={
                'content': disclaimer_content,
                'active': True
            }
        )
        self.stdout.write(self.style.SUCCESS(f'✓ {"Created" if created else "Found"} disclaimer: v{disclaimer.version}'))

        # Create default Package
        package, created = ClassPackage.objects.get_or_create(
            name='5 Session Pass',
            defaults={
                'description': 'Package of 5 sessions at a discounted rate',
                'class_count': 5,
                'price': Decimal('200.00'),
                'validity_days': 90,
                'active': True
            }
        )
        self.stdout.write(self.style.SUCCESS(f'✓ {"Created" if created else "Found"} package: {package.name}'))

        self.stdout.write(self.style.SUCCESS('\n✅ Production setup complete!'))
