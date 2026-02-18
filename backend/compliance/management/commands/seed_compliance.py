"""
Seed UK baseline compliance items with legal references.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from compliance.models import ComplianceCategory, ComplianceItem


UK_BASELINE = [
    {
        'category': 'Fire Safety',
        'items': [
            {
                'title': 'Fire Risk Assessment',
                'item_type': 'LEGAL',
                'frequency_type': 'annual',
                'evidence_required': True,
                'regulatory_ref': 'RRFSO Art.9',
                'legal_reference': 'Regulatory Reform (Fire Safety) Order 2005, Article 9',
                'description': 'A suitable and sufficient fire risk assessment must be carried out and reviewed regularly.',
                'plain_english_why': 'You are legally required to have this. Without it you could be fined if inspected.',
                'primary_action': 'Create now',
            },
            {
                'title': 'Fire Extinguisher Service',
                'item_type': 'LEGAL',
                'frequency_type': 'annual',
                'evidence_required': True,
                'regulatory_ref': 'RRFSO Art.13',
                'legal_reference': 'Regulatory Reform (Fire Safety) Order 2005, Article 13; BS 5306-3',
                'description': 'All fire extinguishers must be serviced annually by a competent person.',
                'plain_english_why': 'If your extinguishers are not serviced they may not work in a fire. You could be liable.',
                'primary_action': 'Book service',
            },
            {
                'title': 'Emergency Lighting Annual Test',
                'item_type': 'LEGAL',
                'frequency_type': 'annual',
                'evidence_required': True,
                'regulatory_ref': 'BS 5266-1',
                'legal_reference': 'BS 5266-1:2016 Emergency Lighting; RRFSO Article 14',
                'description': 'Full duration discharge test of emergency lighting (3 hours).',
                'plain_english_why': 'Emergency lights must work during a power cut. Testing proves they do.',
                'primary_action': 'Book testing',
            },
            {
                'title': 'Fire Alarm System Service',
                'item_type': 'LEGAL',
                'frequency_type': 'quarterly',
                'evidence_required': True,
                'regulatory_ref': 'BS 5839-1',
                'legal_reference': 'BS 5839-1:2017 Fire Detection and Alarm Systems',
                'description': 'Fire alarm system must be serviced quarterly by a competent person.',
                'plain_english_why': 'Your fire alarm must be tested regularly. If it fails during a fire, you are liable.',
                'primary_action': 'Book service',
            },
            {
                'title': 'Fire Drill',
                'item_type': 'BEST_PRACTICE',
                'frequency_type': 'annual',
                'evidence_required': False,
                'regulatory_ref': 'RRFSO Art.21',
                'legal_reference': 'Regulatory Reform (Fire Safety) Order 2005, Article 21',
                'description': 'Practice evacuation drill. Record date, time taken, and any issues.',
                'plain_english_why': 'Staff need to know what to do in a fire. A drill proves they do.',
                'primary_action': 'Schedule drill',
            },
        ],
    },
    {
        'category': 'Electrical Safety',
        'items': [
            {
                'title': 'Electrical Installation Condition Report (EICR)',
                'item_type': 'LEGAL',
                'frequency_type': '5_year',
                'evidence_required': True,
                'regulatory_ref': 'EAWR Reg.4',
                'legal_reference': 'Electricity at Work Regulations 1989, Regulation 4; BS 7671',
                'description': 'Fixed wiring inspection and testing by a qualified electrician. Required every 5 years for commercial premises.',
                'plain_english_why': 'Your building wiring must be safe. An EICR proves it is. Required every 5 years.',
                'primary_action': 'Book inspection',
            },
            {
                'title': 'PAT Testing',
                'item_type': 'BEST_PRACTICE',
                'frequency_type': 'annual',
                'evidence_required': True,
                'regulatory_ref': 'EAWR Reg.4',
                'legal_reference': 'Electricity at Work Regulations 1989 (best practice, not explicitly mandated)',
                'description': 'Portable Appliance Testing. Not a legal requirement but strongly recommended by HSE.',
                'plain_english_why': 'If a faulty appliance injures someone and you have not tested it, you could be liable.',
                'primary_action': 'Book testing',
            },
        ],
    },
    {
        'category': 'Insurance & Legal',
        'items': [
            {
                'title': "Employers' Liability Insurance",
                'item_type': 'LEGAL',
                'frequency_type': 'annual',
                'evidence_required': True,
                'regulatory_ref': 'ELCIA 1969',
                'legal_reference': "Employers' Liability (Compulsory Insurance) Act 1969",
                'description': 'Must hold at least £5 million EL insurance. Certificate must be displayed or accessible.',
                'plain_english_why': 'Required by law if you employ anyone. Without it you can be fined £2,500 per day.',
                'primary_action': 'Upload certificate',
            },
            {
                'title': 'Public Liability Insurance',
                'item_type': 'BEST_PRACTICE',
                'frequency_type': 'annual',
                'evidence_required': True,
                'regulatory_ref': '',
                'legal_reference': 'Not legally required but essential for client-facing businesses',
                'description': 'Public liability insurance covering injury to clients and visitors.',
                'plain_english_why': 'If a customer is injured on your premises and you are not insured, you pay out of pocket.',
                'primary_action': 'Upload certificate',
            },
        ],
    },
    {
        'category': 'First Aid & Welfare',
        'items': [
            {
                'title': 'First Aid Provision Review',
                'item_type': 'LEGAL',
                'frequency_type': 'annual',
                'evidence_required': False,
                'regulatory_ref': 'HSWA s.2; FAR 1981',
                'legal_reference': 'Health and Safety (First-Aid) Regulations 1981',
                'description': 'Review first aid needs assessment, check kit contents, and ensure appointed person is current.',
                'plain_english_why': 'You must have first aid available. If someone is hurt and you have nothing, that is a problem.',
                'primary_action': 'Review now',
            },
            {
                'title': 'First Aid Kit Check',
                'item_type': 'BEST_PRACTICE',
                'frequency_type': 'monthly',
                'evidence_required': False,
                'regulatory_ref': 'FAR 1981',
                'legal_reference': 'Health and Safety (First-Aid) Regulations 1981',
                'description': 'Monthly check of first aid kit contents. Replace used or expired items.',
                'plain_english_why': 'An empty first aid kit is useless. Check it monthly so it is ready when needed.',
                'primary_action': 'Mark checked',
            },
        ],
    },
    {
        'category': 'Risk Assessments',
        'items': [
            {
                'title': 'General Risk Assessment Review',
                'item_type': 'LEGAL',
                'frequency_type': 'annual',
                'evidence_required': True,
                'regulatory_ref': 'MHSWR Reg.3',
                'legal_reference': 'Management of Health and Safety at Work Regulations 1999, Regulation 3',
                'description': 'Review and update all workplace risk assessments. Must be suitable and sufficient.',
                'plain_english_why': 'You must identify what could hurt people in your workplace and write it down.',
                'primary_action': 'Create now',
            },
            {
                'title': 'COSHH Assessment Review',
                'item_type': 'LEGAL',
                'frequency_type': 'annual',
                'evidence_required': True,
                'regulatory_ref': 'COSHH Reg.6',
                'legal_reference': 'Control of Substances Hazardous to Health Regulations 2002, Regulation 6',
                'description': 'Review COSHH assessments for all hazardous substances used on premises.',
                'plain_english_why': 'If you use chemicals (cleaning products count), you must assess the risks.',
                'primary_action': 'Review now',
            },
            {
                'title': 'Display Screen Equipment Assessment',
                'item_type': 'LEGAL',
                'frequency_type': 'annual',
                'evidence_required': False,
                'regulatory_ref': 'DSE Regs 1992',
                'legal_reference': 'Health and Safety (Display Screen Equipment) Regulations 1992',
                'description': 'Workstation assessment for regular DSE users.',
                'plain_english_why': 'If staff use computers regularly, you must check their workstation is set up safely.',
                'primary_action': 'Assess now',
            },
        ],
    },
    {
        'category': 'Gas Safety',
        'items': [
            {
                'title': 'Gas Safety Certificate (CP12)',
                'item_type': 'LEGAL',
                'frequency_type': 'annual',
                'evidence_required': True,
                'regulatory_ref': 'GSIUR Reg.36',
                'legal_reference': 'Gas Safety (Installation and Use) Regulations 1998, Regulation 36',
                'description': 'Annual gas safety check by a Gas Safe registered engineer. Required if gas appliances are present.',
                'plain_english_why': 'If you have gas appliances, they must be checked yearly. A gas leak can kill.',
                'primary_action': 'Book engineer',
            },
        ],
    },
    {
        'category': 'General Compliance',
        'items': [
            {
                'title': 'Health & Safety Law Poster',
                'item_type': 'LEGAL',
                'frequency_type': 'ad_hoc',
                'evidence_required': False,
                'regulatory_ref': 'HSWA s.2',
                'legal_reference': 'Health and Safety Information for Employees Regulations 2009',
                'description': 'HSE approved law poster must be displayed or equivalent leaflet provided to all employees.',
                'plain_english_why': 'You must display the HSE law poster where staff can see it. Costs about £5.',
                'primary_action': 'Mark done',
            },
            {
                'title': 'Accident Book (BI 510)',
                'item_type': 'LEGAL',
                'frequency_type': 'ad_hoc',
                'evidence_required': False,
                'regulatory_ref': 'SS(CA)R 1989',
                'legal_reference': 'Social Security (Claims and Payments) Regulations 1979',
                'description': 'Accident book must be available for recording workplace accidents. GDPR-compliant version required.',
                'plain_english_why': 'You must record all workplace accidents. Buy a GDPR-compliant accident book.',
                'primary_action': 'Mark done',
            },
            {
                'title': 'Health & Safety Policy',
                'item_type': 'LEGAL',
                'frequency_type': 'annual',
                'evidence_required': True,
                'regulatory_ref': 'HSWA s.2(3)',
                'legal_reference': 'Health and Safety at Work etc. Act 1974, Section 2(3)',
                'description': 'Written health and safety policy required if you employ 5 or more people.',
                'plain_english_why': 'If you have 5+ staff you must have a written H&S policy. It shows how you keep people safe.',
                'primary_action': 'Create now',
            },
            {
                'title': 'Training Records',
                'item_type': 'LEGAL',
                'frequency_type': 'ad_hoc',
                'evidence_required': False,
                'regulatory_ref': 'MHSWR Reg.13',
                'legal_reference': 'Management of Health and Safety at Work Regulations 1999, Regulation 13',
                'description': 'Records of all health and safety training provided to employees.',
                'plain_english_why': 'You must be able to prove staff have been trained. Keep records of all training.',
                'primary_action': 'Upload records',
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed UK baseline compliance items with legal references (per tenant)'

    def add_arguments(self, parser):
        parser.add_argument('--tenant', type=str, help='Seed only a specific tenant slug')

    def handle(self, *args, **options):
        from tenants.models import TenantSettings
        from compliance.models import PeaceOfMindScore

        # Disconnect signal to avoid recalculate during bulk creation
        from django.db.models.signals import post_save, post_delete
        from compliance.signals import recalculate_score_on_save, recalculate_score_on_delete
        post_save.disconnect(recalculate_score_on_save)
        post_delete.disconnect(recalculate_score_on_delete)

        target_slug = options.get('tenant')
        if target_slug:
            tenants = TenantSettings.objects.filter(slug=target_slug)
        else:
            tenants = TenantSettings.objects.all()

        if not tenants.exists():
            self.stderr.write('No tenants found. Run seed_demo first.')
            return

        today = timezone.now().date()

        for tenant in tenants:
            self.stdout.write(f'\nSeeding UK compliance baseline for {tenant.business_name or tenant.slug}...')
            created_count = 0

            for cat_data in UK_BASELINE:
                try:
                    cat, _ = ComplianceCategory.objects.get_or_create(
                        tenant=tenant, name=cat_data['category'],
                        defaults={'max_score': 10}
                    )
                    self.stdout.write(f'  Category: {cat.name}')

                    for item_data in cat_data['items']:
                        try:
                            obj, created = ComplianceItem.objects.get_or_create(
                                title=item_data['title'],
                                category=cat,
                                defaults={
                                    'description': item_data['description'],
                                    'item_type': item_data['item_type'],
                                    'frequency_type': item_data['frequency_type'],
                                    'evidence_required': item_data['evidence_required'],
                                    'regulatory_ref': item_data['regulatory_ref'],
                                    'legal_reference': item_data['legal_reference'],
                                    'plain_english_why': item_data.get('plain_english_why', ''),
                                    'primary_action': item_data.get('primary_action', ''),
                                    'next_due_date': today + timedelta(days=30),
                                    'due_date': today + timedelta(days=30),
                                    'status': 'DUE_SOON',
                                }
                            )
                            # Always update Wiggum fields on existing items
                            if not created:
                                obj.plain_english_why = item_data.get('plain_english_why', '')
                                obj.primary_action = item_data.get('primary_action', '')
                                obj.description = item_data['description']
                                obj.legal_reference = item_data['legal_reference']
                                obj.save(update_fields=['plain_english_why', 'primary_action', 'description', 'legal_reference'])
                            if created:
                                created_count += 1
                                self.stdout.write(f'    + {item_data["title"]}')
                            else:
                                self.stdout.write(f'    = {item_data["title"]} (updated)')
                        except Exception as e:
                            self.stderr.write(f'    ERROR creating {item_data["title"]}: {e}')
                except Exception as e:
                    self.stderr.write(f'  ERROR with category {cat_data["category"]}: {e}')

            self.stdout.write(self.style.SUCCESS(f'  Seeded {created_count} new items for {tenant.slug}.'))

            # Recalculate score for this tenant
            try:
                PeaceOfMindScore.recalculate(tenant=tenant)
                self.stdout.write(self.style.SUCCESS(f'  Peace of Mind Score recalculated for {tenant.slug}.'))
            except Exception as e:
                self.stderr.write(f'  Score recalculation error for {tenant.slug}: {e}')

        # Reconnect signals after all seeding + recalculation is done
        post_save.connect(recalculate_score_on_save)
        post_delete.connect(recalculate_score_on_delete)
