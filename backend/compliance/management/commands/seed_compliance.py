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
            },
            {
                'title': 'Fire Extinguisher Service',
                'item_type': 'LEGAL',
                'frequency_type': 'annual',
                'evidence_required': True,
                'regulatory_ref': 'RRFSO Art.13',
                'legal_reference': 'Regulatory Reform (Fire Safety) Order 2005, Article 13; BS 5306-3',
                'description': 'All fire extinguishers must be serviced annually by a competent person.',
            },
            {
                'title': 'Emergency Lighting Annual Test',
                'item_type': 'LEGAL',
                'frequency_type': 'annual',
                'evidence_required': True,
                'regulatory_ref': 'BS 5266-1',
                'legal_reference': 'BS 5266-1:2016 Emergency Lighting; RRFSO Article 14',
                'description': 'Full duration discharge test of emergency lighting (3 hours).',
            },
            {
                'title': 'Fire Alarm System Service',
                'item_type': 'LEGAL',
                'frequency_type': 'quarterly',
                'evidence_required': True,
                'regulatory_ref': 'BS 5839-1',
                'legal_reference': 'BS 5839-1:2017 Fire Detection and Alarm Systems',
                'description': 'Fire alarm system must be serviced quarterly by a competent person.',
            },
            {
                'title': 'Fire Drill',
                'item_type': 'BEST_PRACTICE',
                'frequency_type': 'annual',
                'evidence_required': False,
                'regulatory_ref': 'RRFSO Art.21',
                'legal_reference': 'Regulatory Reform (Fire Safety) Order 2005, Article 21',
                'description': 'Practice evacuation drill. Record date, time taken, and any issues.',
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
            },
            {
                'title': 'PAT Testing',
                'item_type': 'BEST_PRACTICE',
                'frequency_type': 'annual',
                'evidence_required': True,
                'regulatory_ref': 'EAWR Reg.4',
                'legal_reference': 'Electricity at Work Regulations 1989 (best practice, not explicitly mandated)',
                'description': 'Portable Appliance Testing. Not a legal requirement but strongly recommended by HSE.',
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
            },
            {
                'title': 'Public Liability Insurance',
                'item_type': 'BEST_PRACTICE',
                'frequency_type': 'annual',
                'evidence_required': True,
                'regulatory_ref': '',
                'legal_reference': 'Not legally required but essential for client-facing businesses',
                'description': 'Public liability insurance covering injury to clients and visitors.',
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
            },
            {
                'title': 'First Aid Kit Check',
                'item_type': 'BEST_PRACTICE',
                'frequency_type': 'monthly',
                'evidence_required': False,
                'regulatory_ref': 'FAR 1981',
                'legal_reference': 'Health and Safety (First-Aid) Regulations 1981',
                'description': 'Monthly check of first aid kit contents. Replace used or expired items.',
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
            },
            {
                'title': 'COSHH Assessment Review',
                'item_type': 'LEGAL',
                'frequency_type': 'annual',
                'evidence_required': True,
                'regulatory_ref': 'COSHH Reg.6',
                'legal_reference': 'Control of Substances Hazardous to Health Regulations 2002, Regulation 6',
                'description': 'Review COSHH assessments for all hazardous substances used on premises.',
            },
            {
                'title': 'Display Screen Equipment Assessment',
                'item_type': 'LEGAL',
                'frequency_type': 'annual',
                'evidence_required': False,
                'regulatory_ref': 'DSE Regs 1992',
                'legal_reference': 'Health and Safety (Display Screen Equipment) Regulations 1992',
                'description': 'Workstation assessment for regular DSE users.',
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
            },
            {
                'title': 'Accident Book (BI 510)',
                'item_type': 'LEGAL',
                'frequency_type': 'ad_hoc',
                'evidence_required': False,
                'regulatory_ref': 'SS(CA)R 1989',
                'legal_reference': 'Social Security (Claims and Payments) Regulations 1979',
                'description': 'Accident book must be available for recording workplace accidents. GDPR-compliant version required.',
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed UK baseline compliance items with legal references'

    def handle(self, *args, **options):
        self.stdout.write('Seeding UK compliance baseline...')

        # Disconnect signal to avoid recalculate during bulk creation
        from django.db.models.signals import post_save, post_delete
        from compliance.signals import recalculate_score_on_save, recalculate_score_on_delete
        post_save.disconnect(recalculate_score_on_save)
        post_delete.disconnect(recalculate_score_on_delete)

        today = timezone.now().date()
        created_count = 0

        for cat_data in UK_BASELINE:
            try:
                cat, _ = ComplianceCategory.objects.get_or_create(
                    name=cat_data['category'],
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
                                'next_due_date': today + timedelta(days=30),
                                'due_date': today + timedelta(days=30),
                                'status': 'DUE_SOON',
                            }
                        )
                        if created:
                            created_count += 1
                            self.stdout.write(f'    + {item_data["title"]}')
                        else:
                            self.stdout.write(f'    = {item_data["title"]} (exists)')
                    except Exception as e:
                        self.stderr.write(f'    ERROR creating {item_data["title"]}: {e}')
            except Exception as e:
                self.stderr.write(f'  ERROR with category {cat_data["category"]}: {e}')

        self.stdout.write(self.style.SUCCESS(f'\nSeeded {created_count} compliance items.'))

        # Recalculate score (keep signals disconnected to avoid recursion)
        try:
            from compliance.models import PeaceOfMindScore
            PeaceOfMindScore.recalculate()
            self.stdout.write(self.style.SUCCESS('Peace of Mind Score recalculated.'))
        except Exception as e:
            self.stderr.write(f'Score recalculation error: {e}')

        # Reconnect signals after all seeding + recalculation is done
        post_save.connect(recalculate_score_on_save)
        post_delete.connect(recalculate_score_on_delete)
