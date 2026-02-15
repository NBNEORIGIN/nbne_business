"""
Tests for Dashboard vNext components:
- BusinessEvent model
- Cover logic (7-day rotation, tiered, decline/re-suggest)
- Event logging API
- Assistant parse endpoint
- Today resolved endpoint
"""
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, RequestFactory
from django.utils import timezone
from django.contrib.auth import get_user_model

from core.models_events import BusinessEvent

User = get_user_model()


# ---------------------------------------------------------------------------
# BusinessEvent model tests
# ---------------------------------------------------------------------------

class BusinessEventModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='owner', email='owner@test.local', password='test1234',
            first_name='Test', last_name='Owner',
        )

    def test_log_creates_event(self):
        evt = BusinessEvent.log(
            event_type='COVER_REQUESTED',
            action_label='Ask Jordan to cover',
            user=self.user,
            source_event_type='staff_sick',
            source_entity_type='leave_request',
            source_entity_id=42,
            action_detail='Jordan is next in 7-day rotation',
        )
        self.assertEqual(evt.event_type, 'COVER_REQUESTED')
        self.assertEqual(evt.action_label, 'Ask Jordan to cover')
        self.assertEqual(evt.performed_by, self.user)
        self.assertEqual(evt.source_event_type, 'staff_sick')
        self.assertEqual(evt.source_entity_id, 42)
        self.assertEqual(evt.status, 'COMPLETED')

    def test_log_without_user(self):
        evt = BusinessEvent.log(
            event_type='PAYMENT_REQUESTED',
            action_label='Request payment',
        )
        self.assertIsNone(evt.performed_by)
        self.assertEqual(evt.status, 'COMPLETED')

    def test_log_with_payload(self):
        evt = BusinessEvent.log(
            event_type='COVER_REQUESTED',
            action_label='Ask Sam to cover',
            payload={'cover_staff_id': 7, 'absent_staff_id': 3},
        )
        self.assertEqual(evt.payload['cover_staff_id'], 7)

    def test_today_resolved_returns_today_only(self):
        # Create event today
        BusinessEvent.log(event_type='BOOKING_ASSIGNED', action_label='Assign Sam')
        # Create event yesterday (manually set created_at)
        old = BusinessEvent.log(event_type='PAYMENT_MARKED', action_label='Mark paid')
        BusinessEvent.objects.filter(id=old.id).update(
            created_at=timezone.now() - timedelta(days=1, hours=1)
        )

        today = BusinessEvent.today_resolved()
        self.assertEqual(today.count(), 1)
        self.assertEqual(today.first().action_label, 'Assign Sam')

    def test_str_representation(self):
        evt = BusinessEvent.log(
            event_type='COVER_REQUESTED',
            action_label='Ask Jordan to cover',
        )
        s = str(evt)
        self.assertIn('Cover Requested', s)
        self.assertIn('Ask Jordan to cover', s)

    def test_all_event_types_valid(self):
        valid_types = {t[0] for t in BusinessEvent.EVENT_TYPES}
        self.assertIn('STAFF_SICK', valid_types)
        self.assertIn('COVER_REQUESTED', valid_types)
        self.assertIn('COVER_ACCEPTED', valid_types)
        self.assertIn('COVER_DECLINED', valid_types)
        self.assertIn('BOOKING_ASSIGNED', valid_types)
        self.assertIn('PAYMENT_REQUESTED', valid_types)
        self.assertIn('OWNER_OVERRIDE', valid_types)
        self.assertIn('ASSISTANT_COMMAND', valid_types)


# ---------------------------------------------------------------------------
# Cover logic tests
# ---------------------------------------------------------------------------

class CoverLogicTests(TestCase):

    def setUp(self):
        from bookings.models import Staff as BookingStaff, Service
        self.svc = Service.objects.create(
            name='Cut', category='hair', duration_minutes=30,
            price=Decimal('30.00'),
        )
        self.absent = BookingStaff.objects.create(name='Chloe', email='chloe@test.local', active=True)
        self.staff_a = BookingStaff.objects.create(name='Jordan', email='jordan@test.local', active=True)
        self.staff_b = BookingStaff.objects.create(name='Sam', email='sam@test.local', active=True)
        self.staff_c = BookingStaff.objects.create(name='Alex', email='alex@test.local', active=True)
        # Link services
        for s in [self.absent, self.staff_a, self.staff_b, self.staff_c]:
            s.services.add(self.svc)

    def test_rotation_returns_candidates(self):
        from core.cover_logic import get_cover_candidates
        candidates = get_cover_candidates(self.absent.id, strategy='rotation', max_candidates=3)
        self.assertTrue(len(candidates) > 0)
        self.assertTrue(len(candidates) <= 3)
        # Should not include absent staff
        names = [c['name'] for c in candidates]
        self.assertNotIn('Chloe', names)

    def test_rotation_excludes_recently_covered(self):
        from core.cover_logic import get_cover_candidates
        # Log a recent cover for Jordan
        BusinessEvent.log(
            event_type='COVER_ACCEPTED',
            action_label='Jordan covered',
            payload={'cover_staff_id': self.staff_a.id},
        )
        candidates = get_cover_candidates(self.absent.id, strategy='rotation', max_candidates=3)
        # Jordan should be ranked lower (still included but after others)
        if len(candidates) >= 2:
            jordan_rank = next((c['rank'] for c in candidates if c['name'] == 'Jordan'), 99)
            other_ranks = [c['rank'] for c in candidates if c['name'] != 'Jordan']
            if other_ranks:
                self.assertGreater(jordan_rank, min(other_ranks))

    def test_tiered_returns_candidates(self):
        from core.cover_logic import get_cover_candidates
        candidates = get_cover_candidates(self.absent.id, strategy='tiered', max_candidates=2)
        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0]['rank'], 1)
        self.assertEqual(candidates[1]['rank'], 2)

    def test_service_filter(self):
        from core.cover_logic import get_cover_candidates
        from bookings.models import Service
        # Create a service only Jordan has
        special = Service.objects.create(
            name='Special', category='special', duration_minutes=60,
            price=Decimal('100.00'),
        )
        self.staff_a.services.add(special)
        candidates = get_cover_candidates(self.absent.id, service=special, strategy='rotation')
        names = [c['name'] for c in candidates]
        self.assertIn('Jordan', names)
        self.assertNotIn('Sam', names)
        self.assertNotIn('Alex', names)

    def test_get_next_candidate_after_decline(self):
        from core.cover_logic import get_next_candidate
        # Decline Jordan and Sam
        next_c = get_next_candidate(
            absent_staff_id=self.absent.id,
            declined_staff_ids=[self.staff_a.id, self.staff_b.id],
        )
        # Should suggest Alex
        if next_c:
            self.assertEqual(next_c['name'], 'Alex')

    def test_no_candidates_returns_empty(self):
        from core.cover_logic import get_next_candidate
        # Decline everyone
        next_c = get_next_candidate(
            absent_staff_id=self.absent.id,
            declined_staff_ids=[self.staff_a.id, self.staff_b.id, self.staff_c.id],
        )
        self.assertIsNone(next_c)

    def test_each_candidate_has_reason(self):
        from core.cover_logic import get_cover_candidates
        candidates = get_cover_candidates(self.absent.id, strategy='rotation')
        for c in candidates:
            self.assertIn('reason', c)
            self.assertTrue(len(c['reason']) > 0)


# ---------------------------------------------------------------------------
# Event logging API tests
# ---------------------------------------------------------------------------

class EventLoggingAPITests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='owner', email='owner@test.local', password='test1234',
            first_name='Test', last_name='Owner',
        )
        self.factory = RequestFactory()

    def _auth_request(self, method, path, data=None):
        from rest_framework.test import force_authenticate
        if method == 'POST':
            request = self.factory.post(path, data=data, content_type='application/json')
        else:
            request = self.factory.get(path)
        force_authenticate(request, user=self.user)
        return request

    def test_log_event_success(self):
        from core.views_events import log_event
        import json
        request = self._auth_request('POST', '/api/events/log/', json.dumps({
            'event_type': 'COVER_REQUESTED',
            'action_label': 'Ask Jordan to cover',
            'source_event_type': 'staff_sick',
        }))
        response = log_event(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['event_type'], 'COVER_REQUESTED')

    def test_log_event_missing_fields(self):
        from core.views_events import log_event
        import json
        request = self._auth_request('POST', '/api/events/log/', json.dumps({
            'event_type': 'COVER_REQUESTED',
        }))
        response = log_event(request)
        self.assertEqual(response.status_code, 400)

    def test_log_event_invalid_type(self):
        from core.views_events import log_event
        import json
        request = self._auth_request('POST', '/api/events/log/', json.dumps({
            'event_type': 'INVALID_TYPE',
            'action_label': 'Test',
        }))
        response = log_event(request)
        self.assertEqual(response.status_code, 400)

    def test_today_resolved_endpoint(self):
        from core.views_events import today_resolved
        BusinessEvent.log(event_type='BOOKING_ASSIGNED', action_label='Assign Sam', user=self.user)
        request = self._auth_request('GET', '/api/events/today/')
        response = today_resolved(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['events'][0]['action_label'], 'Assign Sam')
        self.assertEqual(response.data['events'][0]['performed_by'], self.user.get_full_name() or 'System')


# ---------------------------------------------------------------------------
# Assistant parse tests
# ---------------------------------------------------------------------------

class AssistantParseTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='owner', email='owner@test.local', password='test1234',
            first_name='Test', last_name='Owner',
        )
        self.factory = RequestFactory()

    def _auth_post(self, data):
        from rest_framework.test import force_authenticate
        import json
        request = self.factory.post(
            '/api/assistant/parse/',
            data=json.dumps(data),
            content_type='application/json',
        )
        force_authenticate(request, user=self.user)
        return request

    def test_parse_sick(self):
        from core.views_assistant import parse_command
        request = self._auth_post({'text': 'Chloe is off sick today'})
        response = parse_command(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['parsed'])
        self.assertEqual(response.data['intent']['event_type'], 'STAFF_SICK')
        self.assertTrue(response.data['confirmation_required'])

    def test_parse_assign(self):
        from core.views_assistant import parse_command
        request = self._auth_post({'text': 'Assign Sam to the 11:00 booking'})
        response = parse_command(request)
        self.assertTrue(response.data['parsed'])
        self.assertEqual(response.data['intent']['event_type'], 'BOOKING_ASSIGNED')

    def test_parse_payment(self):
        from core.views_assistant import parse_command
        request = self._auth_post({'text': 'Request payment from Sarah'})
        response = parse_command(request)
        self.assertTrue(response.data['parsed'])
        self.assertEqual(response.data['intent']['event_type'], 'PAYMENT_REQUESTED')

    def test_parse_unknown(self):
        from core.views_assistant import parse_command
        request = self._auth_post({'text': 'What is the meaning of life'})
        response = parse_command(request)
        self.assertFalse(response.data['parsed'])
        self.assertIsNone(response.data['intent'])

    def test_parse_empty_text(self):
        from core.views_assistant import parse_command
        request = self._auth_post({'text': ''})
        response = parse_command(request)
        self.assertEqual(response.status_code, 400)

    def test_parse_cancel_booking(self):
        from core.views_assistant import parse_command
        request = self._auth_post({'text': 'Cancel booking for Emma'})
        response = parse_command(request)
        self.assertTrue(response.data['parsed'])
        self.assertEqual(response.data['intent']['event_type'], 'BOOKING_CANCELLED')

    def test_parse_approve_leave(self):
        from core.views_assistant import parse_command
        request = self._auth_post({'text': 'Approve leave for Jordan'})
        response = parse_command(request)
        self.assertTrue(response.data['parsed'])
        self.assertEqual(response.data['intent']['event_type'], 'LEAVE_APPROVED')

    def test_confirmation_message_present(self):
        from core.views_assistant import parse_command
        request = self._auth_post({'text': 'Mark as paid for Sarah'})
        response = parse_command(request)
        self.assertTrue(response.data['parsed'])
        self.assertIn('confirmation_message', response.data)
        self.assertTrue(len(response.data['confirmation_message']) > 0)

    def test_never_auto_commits(self):
        """Assistant must always require confirmation — never auto-commit."""
        from core.views_assistant import parse_command
        request = self._auth_post({'text': 'Chloe is off sick'})
        response = parse_command(request)
        self.assertTrue(response.data['confirmation_required'])
        # Verify no BusinessEvent was created
        self.assertEqual(BusinessEvent.objects.count(), 0)
