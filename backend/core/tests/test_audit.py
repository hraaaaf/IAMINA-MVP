"""
AuditLog behaviour — creation, nullable actor, default metadata, anonymous
actions. The middleware that populates it lands in Phase 5.
"""
from django.contrib.auth.models import User
from django.test import TestCase

from core.models import AuditLog


class AuditLogModelTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='pw')

    def test_create_and_retrieve(self):
        entry = AuditLog.objects.create(
            actor=self.alice,
            action='login',
            resource_type='User',
            resource_id=str(self.alice.pk),
            metadata={'source': 'web'},
            ip_address='127.0.0.1',
            user_agent='test-agent/1.0',
        )
        self.assertEqual(entry.action, 'login')
        self.assertEqual(entry.metadata, {'source': 'web'})
        self.assertEqual(entry.ip_address, '127.0.0.1')

    def test_actor_set_null_when_user_deleted(self):
        entry = AuditLog.objects.create(actor=self.alice, action='view', resource_type='LogEntry')
        self.alice.delete()
        entry.refresh_from_db()
        self.assertIsNone(entry.actor)

    def test_default_metadata_is_empty_dict(self):
        entry = AuditLog.objects.create(actor=self.alice, action='view', resource_type='LogEntry')
        self.assertEqual(entry.metadata, {})

    def test_anonymous_action_allowed(self):
        entry = AuditLog.objects.create(action='login', resource_type='User', metadata={'success': False})
        self.assertIsNone(entry.actor)
