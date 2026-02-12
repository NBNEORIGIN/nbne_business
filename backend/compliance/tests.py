"""
Phase 7 & 9: Compliance module tests.
Covers: model logic, scheduling, RBAC enforcement, API endpoints, tenant isolation.
"""
from datetime import date, timedelta
from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from .models import (
    ComplianceCategory, ComplianceItem, IncidentReport, TrainingRecord,
    DocumentVault, ComplianceActionLog,
)

User = get_user_model()


class ComplianceItemModelTests(TestCase):
    """Test ComplianceItem scheduling logic."""

    def setUp(self):
        self.cat = ComplianceCategory.objects.create(
            name='Fire Safety', legal_requirement=True, order=1,
        )

    def test_frequency_in_days(self):
        item = ComplianceItem(frequency_type='annual')
        self.assertEqual(item.frequency_in_days, 365)
        item.frequency_type = '3_year'
        self.assertEqual(item.frequency_in_days, 1095)
        item.frequency_type = '5_year'
        self.assertEqual(item.frequency_in_days, 1825)
        item.frequency_type = 'weekly'
        self.assertEqual(item.frequency_in_days, 7)
        item.frequency_type = 'one_off'
        self.assertIsNone(item.frequency_in_days)
        item.frequency_type = 'custom_days'
        item.frequency_days = 90
        self.assertEqual(item.frequency_in_days, 90)

    def test_calculate_next_due(self):
        item = ComplianceItem(
            title='Test', category=self.cat,
            frequency_type='annual',
            last_completed_date=date(2025, 6, 1),
        )
        self.assertEqual(item.calculate_next_due(), date(2026, 6, 1))

    def test_calculate_next_due_one_off(self):
        item = ComplianceItem(
            title='Test', category=self.cat,
            frequency_type='one_off',
            last_completed_date=date(2025, 6, 1),
        )
        self.assertIsNone(item.calculate_next_due())

    def test_update_status_overdue(self):
        item = ComplianceItem(
            title='Test', category=self.cat,
            frequency_type='annual',
            next_due_date=date.today() - timedelta(days=5),
        )
        item.update_status()
        self.assertEqual(item.status, 'overdue')

    def test_update_status_due_soon(self):
        item = ComplianceItem(
            title='Test', category=self.cat,
            frequency_type='annual',
            next_due_date=date.today() + timedelta(days=15),
        )
        item.update_status()
        self.assertEqual(item.status, 'due_soon')

    def test_update_status_compliant(self):
        item = ComplianceItem(
            title='Test', category=self.cat,
            frequency_type='annual',
            next_due_date=date.today() + timedelta(days=60),
        )
        item.update_status()
        self.assertEqual(item.status, 'compliant')

    def test_mark_completed_recalculates(self):
        item = ComplianceItem.objects.create(
            title='Test', category=self.cat,
            frequency_type='annual',
            next_due_date=date.today() - timedelta(days=5),
            status='overdue',
        )
        item.mark_completed(completed_date=date.today())
        self.assertEqual(item.last_completed_date, date.today())
        self.assertEqual(item.next_due_date, date.today() + timedelta(days=365))
        self.assertIn(item.status, ['compliant', 'due_soon'])

    def test_save_auto_calculates_next_due(self):
        item = ComplianceItem.objects.create(
            title='Test', category=self.cat,
            frequency_type='monthly',
            last_completed_date=date.today(),
        )
        self.assertEqual(item.next_due_date, date.today() + timedelta(days=30))


class TrainingRecordTests(TestCase):
    """Test TrainingRecord status properties."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='staff1', password='test123', role='staff',
            first_name='Test', last_name='Staff',
        )

    def test_expired(self):
        record = TrainingRecord(
            user=self.user, training_type='first_aid',
            issue_date=date(2022, 1, 1),
            expiry_date=date(2025, 1, 1),
        )
        self.assertTrue(record.is_expired)
        self.assertEqual(record.status, 'expired')

    def test_expiring_soon(self):
        record = TrainingRecord(
            user=self.user, training_type='first_aid',
            issue_date=date(2023, 1, 1),
            expiry_date=date.today() + timedelta(days=10),
        )
        self.assertFalse(record.is_expired)
        self.assertTrue(record.is_expiring_soon)
        self.assertEqual(record.status, 'expiring_soon')

    def test_valid(self):
        record = TrainingRecord(
            user=self.user, training_type='first_aid',
            issue_date=date(2025, 1, 1),
            expiry_date=date.today() + timedelta(days=365),
        )
        self.assertFalse(record.is_expired)
        self.assertFalse(record.is_expiring_soon)
        self.assertEqual(record.status, 'valid')


class DocumentVaultTests(TestCase):
    """Test DocumentVault versioning."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='owner1', password='test123', role='owner',
            first_name='Test', last_name='Owner',
        )

    def test_upload_new_version(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        doc = DocumentVault.objects.create(
            title='H&S Policy',
            file=SimpleUploadedFile('policy.pdf', b'content'),
            document_type='policy',
            version='1.0',
            uploaded_by=self.user,
        )
        self.assertTrue(doc.is_current)

        new_file = SimpleUploadedFile('policy_v2.pdf', b'new content')
        new_doc = doc.upload_new_version(file=new_file, uploaded_by=self.user)

        doc.refresh_from_db()
        self.assertFalse(doc.is_current)
        self.assertTrue(new_doc.is_current)
        self.assertEqual(new_doc.version, '1.1')
        self.assertEqual(new_doc.supersedes, doc)


class RBACTests(TestCase):
    """Test role-based access control on compliance endpoints."""

    def setUp(self):
        self.customer = User.objects.create_user(
            username='customer1', password='test123', role='customer',
            first_name='Cust', last_name='Omer',
        )
        self.staff = User.objects.create_user(
            username='staff1', password='test123', role='staff',
            first_name='Staff', last_name='Member',
        )
        self.manager = User.objects.create_user(
            username='manager1', password='test123', role='manager',
            first_name='Man', last_name='Ager',
        )
        self.owner = User.objects.create_user(
            username='owner1', password='test123', role='owner',
            first_name='Own', last_name='Er',
        )
        self.client = APIClient()

    def _login(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')

    def test_customer_cannot_access_dashboard(self):
        self._login(self.customer)
        res = self.client.get('/api/compliance/dashboard/')
        self.assertEqual(res.status_code, 403)

    def test_staff_cannot_access_dashboard(self):
        self._login(self.staff)
        res = self.client.get('/api/compliance/dashboard/')
        self.assertEqual(res.status_code, 403)

    def test_manager_can_access_dashboard(self):
        self._login(self.manager)
        res = self.client.get('/api/compliance/dashboard/')
        self.assertEqual(res.status_code, 200)

    def test_owner_can_access_dashboard(self):
        self._login(self.owner)
        res = self.client.get('/api/compliance/dashboard/')
        self.assertEqual(res.status_code, 200)

    def test_staff_can_report_incident(self):
        self._login(self.staff)
        res = self.client.post('/api/compliance/incidents/create/', {
            'title': 'Test incident',
            'description': 'Test description',
            'severity': 'LOW',
            'incident_date': timezone.now().isoformat(),
        }, format='json')
        self.assertEqual(res.status_code, 201)

    def test_customer_cannot_report_incident(self):
        self._login(self.customer)
        res = self.client.post('/api/compliance/incidents/create/', {
            'title': 'Test incident',
            'description': 'Test description',
            'severity': 'LOW',
            'incident_date': timezone.now().isoformat(),
        }, format='json')
        self.assertEqual(res.status_code, 403)

    def test_staff_can_view_my_actions(self):
        self._login(self.staff)
        res = self.client.get('/api/compliance/my-actions/')
        self.assertEqual(res.status_code, 200)

    def test_staff_can_view_my_training(self):
        self._login(self.staff)
        res = self.client.get('/api/compliance/my-training/')
        self.assertEqual(res.status_code, 200)

    def test_staff_cannot_create_compliance_item(self):
        self._login(self.staff)
        res = self.client.post('/api/compliance/items/create/', {
            'title': 'Test', 'category': 1,
        }, format='json')
        self.assertEqual(res.status_code, 403)

    def test_manager_can_create_category(self):
        self._login(self.manager)
        res = self.client.post('/api/compliance/categories/create/', {
            'name': 'Test Category', 'legal_requirement': True,
        }, format='json')
        self.assertEqual(res.status_code, 201)

    def test_staff_cannot_access_training_list(self):
        self._login(self.staff)
        res = self.client.get('/api/compliance/training/')
        self.assertEqual(res.status_code, 403)

    def test_manager_can_access_training_list(self):
        self._login(self.manager)
        res = self.client.get('/api/compliance/training/')
        self.assertEqual(res.status_code, 200)

    def test_staff_cannot_access_documents(self):
        self._login(self.staff)
        res = self.client.get('/api/compliance/documents/')
        self.assertEqual(res.status_code, 403)

    def test_manager_can_access_calendar(self):
        self._login(self.manager)
        res = self.client.get('/api/compliance/calendar/')
        self.assertEqual(res.status_code, 200)

    def test_staff_cannot_access_action_logs(self):
        self._login(self.staff)
        res = self.client.get('/api/compliance/logs/')
        self.assertEqual(res.status_code, 403)


class ComplianceActionLogTests(TestCase):
    """Test that compliance actions are properly logged."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner1', password='test123', role='owner',
            first_name='Own', last_name='Er',
        )
        self.cat = ComplianceCategory.objects.create(
            name='Fire Safety', legal_requirement=True,
        )
        self.client = APIClient()
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(self.owner)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')

    def test_item_creation_logged(self):
        res = self.client.post('/api/compliance/items/create/', {
            'title': 'Fire Risk Assessment',
            'category': self.cat.id,
            'frequency_type': 'annual',
        }, format='json')
        self.assertEqual(res.status_code, 201)
        log = ComplianceActionLog.objects.filter(action='created').first()
        self.assertIsNotNone(log)
        self.assertIn('Fire Risk Assessment', log.notes)

    def test_item_completion_logged(self):
        item = ComplianceItem.objects.create(
            title='Test Item', category=self.cat,
            frequency_type='annual',
            next_due_date=date.today(),
            status='due_soon',
        )
        res = self.client.post(f'/api/compliance/items/{item.id}/complete/', {}, format='json')
        self.assertEqual(res.status_code, 200)
        log = ComplianceActionLog.objects.filter(action='completed').first()
        self.assertIsNotNone(log)

    def test_incident_creation_logged(self):
        res = self.client.post('/api/compliance/incidents/create/', {
            'title': 'Test incident',
            'description': 'Test',
            'severity': 'LOW',
            'incident_date': timezone.now().isoformat(),
        }, format='json')
        self.assertEqual(res.status_code, 201)
        log = ComplianceActionLog.objects.filter(
            action='created', incident__isnull=False,
        ).first()
        self.assertIsNotNone(log)


class BaselineSeedTests(TestCase):
    """Test UK baseline seeding."""

    def test_seed_creates_categories_and_items(self):
        from django.core.management import call_command
        call_command('seed_uk_baseline')
        cats = ComplianceCategory.objects.count()
        items = ComplianceItem.objects.filter(is_baseline=True).count()
        self.assertGreaterEqual(cats, 6)
        self.assertGreaterEqual(items, 10)

    def test_seed_is_idempotent(self):
        from django.core.management import call_command
        call_command('seed_uk_baseline')
        count1 = ComplianceItem.objects.count()
        call_command('seed_uk_baseline')
        count2 = ComplianceItem.objects.count()
        self.assertEqual(count1, count2)
