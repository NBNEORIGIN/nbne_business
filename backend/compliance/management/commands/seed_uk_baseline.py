"""
Phase 5: Pre-populated UK baseline compliance template.
Creates default categories and 10+ compliance items based on UK H&S law.
Idempotent — safe to run multiple times.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from compliance.models import ComplianceCategory, ComplianceItem


UK_BASELINE = [
    {
        'category': 'Fire Safety',
        'legal': True,
        'order': 1,
        'items': [
            {'title': 'Fire Risk Assessment', 'frequency': 'annual', 'desc': 'Regulatory Reform (Fire Safety) Order 2005 — annual review required'},
            {'title': 'Fire Extinguisher Inspection', 'frequency': 'annual', 'desc': 'BS 5306-3 — annual service by competent person'},
            {'title': 'Fire Alarm Test', 'frequency': 'weekly', 'desc': 'BS 5839-1 — weekly test of fire alarm system'},
            {'title': 'Emergency Lighting Test', 'frequency': 'monthly', 'desc': 'BS 5266-1 — monthly function test, annual full duration test'},
            {'title': 'Fire Marshal Training', 'frequency': 'annual', 'desc': 'At least one trained fire marshal per floor/area'},
        ],
    },
    {
        'category': 'Electrical Safety',
        'legal': True,
        'order': 2,
        'items': [
            {'title': 'Fixed Wiring Inspection (EICR)', 'frequency': '5_year', 'desc': 'Electricity at Work Regulations 1989 — EICR every 5 years'},
            {'title': 'Portable Appliance Testing (PAT)', 'frequency': 'annual', 'desc': 'IET Code of Practice — frequency depends on equipment type'},
        ],
    },
    {
        'category': 'Training',
        'legal': True,
        'order': 3,
        'items': [
            {'title': 'First Aid at Work Certificate', 'frequency': '3_year', 'desc': 'Health and Safety (First-Aid) Regulations 1981 — requalification every 3 years'},
            {'title': 'Manual Handling Training', 'frequency': '3_year', 'desc': 'Manual Handling Operations Regulations 1992'},
        ],
    },
    {
        'category': 'General Compliance',
        'legal': True,
        'order': 4,
        'items': [
            {'title': 'Health & Safety Policy Review', 'frequency': 'annual', 'desc': 'HSWA 1974 s.2(3) — written policy required if 5+ employees, review annually'},
            {'title': 'Risk Assessment Review', 'frequency': 'annual', 'desc': 'Management of Health and Safety at Work Regulations 1999 — suitable and sufficient'},
            {'title': 'Employers Liability Insurance', 'frequency': 'annual', 'desc': 'Employers Liability (Compulsory Insurance) Act 1969 — certificate must be displayed'},
        ],
    },
    {
        'category': 'Equipment',
        'legal': False,
        'order': 5,
        'items': [
            {'title': 'Gas Safety Check (if applicable)', 'frequency': 'annual', 'desc': 'Gas Safety (Installation and Use) Regulations 1998 — annual by Gas Safe engineer'},
        ],
    },
    {
        'category': 'Hygiene & Welfare',
        'legal': False,
        'order': 6,
        'items': [
            {'title': 'Workplace Welfare Facilities Check', 'frequency': 'annual', 'desc': 'Workplace (Health, Safety and Welfare) Regulations 1992 — toilets, drinking water, rest areas'},
            {'title': 'COSHH Assessment Review', 'frequency': 'annual', 'desc': 'Control of Substances Hazardous to Health Regulations 2002'},
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed UK baseline compliance categories and items'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Re-create items even if they exist')

    def handle(self, *args, **options):
        force = options['force']
        created_cats = 0
        created_items = 0
        today = timezone.now().date()

        for cat_data in UK_BASELINE:
            cat, cat_created = ComplianceCategory.objects.get_or_create(
                name=cat_data['category'],
                defaults={
                    'legal_requirement': cat_data['legal'],
                    'order': cat_data['order'],
                    'description': '',
                },
            )
            if cat_created:
                created_cats += 1
                self.stdout.write(f"  Created category: {cat.name}")

            for item_data in cat_data['items']:
                defaults = {
                    'description': item_data['desc'],
                    'frequency_type': item_data['frequency'],
                    'is_baseline': True,
                    'status': 'not_started',
                }
                if force:
                    obj, item_created = ComplianceItem.objects.update_or_create(
                        title=item_data['title'],
                        category=cat,
                        is_baseline=True,
                        defaults=defaults,
                    )
                else:
                    obj, item_created = ComplianceItem.objects.get_or_create(
                        title=item_data['title'],
                        category=cat,
                        is_baseline=True,
                        defaults=defaults,
                    )
                if item_created:
                    created_items += 1

        self.stdout.write(self.style.SUCCESS(
            f"UK baseline seeded: {created_cats} categories, {created_items} items created"
        ))
        total = ComplianceItem.objects.filter(is_baseline=True).count()
        self.stdout.write(f"Total baseline items: {total}")
