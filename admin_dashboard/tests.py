import datetime
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.utils import timezone
from channels.testing import WebsocketCommunicator

from items.models import Item
from claims.models import Claim
from notifications.models import Notification
from .models import AuditLog, EmailDelivery
from .audit import record_audit_log
from .email_service import send_event_email
from .realtime import publish_user_event, publish_admin_event
from .consumers import LiveUpdatesConsumer


class AdminDashboardSecurityAndAccessTest(TestCase):
    """
    Validates role-based access control (RBAC), normal user isolation,
    and staff permission enforcement.
    """

    def setUp(self):
        self.client = Client()
        # Normal user
        self.normal_user = User.objects.create_user(
            username='citizen_jane',
            password='Password123!',
            email='jane@example.com'
        )

        # Staff user without granular permissions
        self.staff_user = User.objects.create_user(
            username='staff_bob',
            password='Password123!',
            email='bob@example.com',
            is_staff=True
        )

        # Superuser
        self.admin_user = User.objects.create_superuser(
            username='super_admin',
            password='Password123!',
            email='admin@example.com'
        )

    def test_anonymous_redirected_from_admin_dashboard(self):
        response = self.client.get('/admin-dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_normal_user_denied_access_to_admin_dashboard(self):
        self.client.login(username='citizen_jane', password='Password123!')
        response = self.client.get('/admin-dashboard/')
        self.assertEqual(response.status_code, 403)

    def test_staff_user_can_access_admin_dashboard(self):
        self.client.login(username='staff_bob', password='Password123!')
        response = self.client.get('/admin-dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Platform Overview")

    def test_superuser_can_access_admin_dashboard(self):
        self.client.login(username='super_admin', password='Password123!')
        response = self.client.get('/admin-dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Platform Overview")


class UserManagementAndAuditTest(TestCase):
    """
    Validates user account status toggle, audit log creation,
    in-app notification, and security notice email dispatch.
    """

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username='admin_boss',
            password='Password123!',
            email='boss@findback.local'
        )
        self.target_user = User.objects.create_user(
            username='spammer_joe',
            password='Password123!',
            email='joe@example.com'
        )

    def test_deactivate_user_with_audit_and_notification(self):
        self.client.login(username='admin_boss', password='Password123!')
        url = f'/admin-dashboard/users/{self.target_user.pk}/'

        response = self.client.post(url, {
            'toggle_status': '1',
            'reason': 'Violated community guidelines by posting fake lost items.'
        })
        self.assertEqual(response.status_code, 302)

        # Refresh from db
        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)

        # Verify audit log was created
        audit = AuditLog.objects.filter(
            target_model__iexact='user',
            target_object_id=str(self.target_user.pk),
            action_type=AuditLog.ActionType.USER_DEACTIVATED
        ).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.actor, self.admin)
        self.assertIn("Violated community guidelines", audit.reason)

        # Verify notification created
        notif = Notification.objects.filter(
            recipient=self.target_user,
            notification_type=Notification.NotificationType.ACCOUNT_STATUS_CHANGED
        ).first()
        self.assertIsNotNone(notif)

        # Verify email delivery recorded
        email_record = EmailDelivery.objects.filter(
            recipient_user=self.target_user,
            event_type=EmailDelivery.EventType.ACCOUNT_STATUS_CHANGED
        ).first()
        self.assertIsNotNone(email_record)

    def test_admin_cannot_deactivate_self(self):
        self.client.login(username='admin_boss', password='Password123!')
        url = f'/admin-dashboard/users/{self.admin.pk}/'

        response = self.client.post(url, {
            'toggle_status': '1',
            'reason': 'Attempting self-deactivation.'
        })
        self.assertEqual(response.status_code, 302)

        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)


class ItemModerationAndVisibilityTest(TestCase):
    """
    Tests item moderation actions, hiding items from public catalog,
    and verifying audit logging.
    """

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username='admin_mod',
            password='Password123!',
            email='mod@findback.local'
        )
        self.reporter = User.objects.create_user(
            username='reporter_alice',
            password='Password123!',
            email='alice@example.com'
        )
        self.item = Item.objects.create(
            user=self.reporter,
            title='Suspicious Diamond Ring',
            description='Found near fountain.',
            category=Item.ItemCategory.JEWELRY,
            item_type=Item.ItemType.FOUND,
            location='Central Plaza',
            date_occurred=datetime.date.today(),
            identification_details='Secret inscription: XYZ123'
        )

    def test_hiding_item_removes_it_from_public_search(self):
        # 1. Initially visible in public search
        resp1 = self.client.get('/items/')
        self.assertContains(resp1, 'Suspicious Diamond Ring')

        # 2. Admin hides the item
        self.client.login(username='admin_mod', password='Password123!')
        url = f'/admin-dashboard/items/{self.item.pk}/'
        response = self.client.post(url, {
            'update_moderation': '1',
            'moderation_status': Item.ModerationStatus.FLAGGED,
            'is_hidden': 'on',
            'moderation_notes': 'Needs proof of custody.',
            'reason': 'Content reported for suspicious origin.'
        })
        self.assertEqual(response.status_code, 302)

        self.item.refresh_from_db()
        self.assertTrue(self.item.is_hidden)
        self.assertEqual(self.item.moderation_status, Item.ModerationStatus.FLAGGED)

        # 3. Public search now excludes the hidden item
        self.client.logout()
        resp2 = self.client.get('/items/')
        self.assertNotContains(resp2, 'Suspicious Diamond Ring')

        # 4. Public item detail returns 404 for unauthenticated visitor
        resp3 = self.client.get(f'/items/view/{self.item.pk}/')
        self.assertEqual(resp3.status_code, 404)

        # 5. Audit log verified
        audit = AuditLog.objects.filter(
            target_model__iexact='item',
            target_object_id=str(self.item.pk),
            action_type=AuditLog.ActionType.ITEM_MODERATED
        ).first()
        self.assertIsNotNone(audit)
        self.assertIn("Content reported for suspicious origin", audit.reason)


class AdminClaimInterventionTest(TestCase):
    """
    Tests administrative claim intervention (approval/rejection)
    and atomic resolution of competing pending claims.
    """

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username='admin_claims',
            password='Password123!',
            email='claims_admin@findback.local'
        )
        self.finder = User.objects.create_user(
            username='finder_dan',
            password='Password123!',
            email='dan@example.com'
        )
        self.claimant_a = User.objects.create_user(
            username='claimant_amy',
            password='Password123!',
            email='amy@example.com'
        )
        self.claimant_b = User.objects.create_user(
            username='claimant_ben',
            password='Password123!',
            email='ben@example.com'
        )

        self.item = Item.objects.create(
            user=self.finder,
            title='MacBook Pro 16',
            description='Found in conference hall.',
            category=Item.ItemCategory.LAPTOP,
            item_type=Item.ItemType.FOUND,
            location='Room 302',
            date_occurred=datetime.date.today(),
            identification_details='Serial: C02G9012'
        )

        self.claim_a = Claim.objects.create(
            item=self.item,
            claimant=self.claimant_a,
            reason='My laptop left in Room 302.',
            verification_answer='Serial matches C02G9012 with Apple sticker'
        )
        self.claim_b = Claim.objects.create(
            item=self.item,
            claimant=self.claimant_b,
            reason='Lost laptop here.',
            verification_answer='Black case'
        )

    def test_admin_intervention_approves_claim_and_supersedes_others(self):
        self.client.login(username='admin_claims', password='Password123!')
        url = f'/admin-dashboard/claims/{self.claim_a.pk}/'

        response = self.client.post(url, {
            'claim_intervention': '1',
            'action': 'APPROVE',
            'reason': 'Claimant provided receipt and exact serial number match.'
        })
        self.assertEqual(response.status_code, 302)

        # Refresh objects
        self.claim_a.refresh_from_db()
        self.claim_b.refresh_from_db()
        self.item.refresh_from_db()

        # Claim A approved
        self.assertEqual(self.claim_a.status, Claim.Status.APPROVED)
        self.assertEqual(self.claim_a.reviewed_by, self.admin)

        # Item marked CLAIMED
        self.assertEqual(self.item.status, Item.ItemStatus.CLAIMED)

        # Competing Claim B superseded (REJECTED)
        self.assertEqual(self.claim_b.status, Claim.Status.REJECTED)
        self.assertIn("Another claim on this item was verified", self.claim_b.reviewer_note)

        # Claimant A receives approved notification
        notif_a = Notification.objects.filter(
            recipient=self.claimant_a,
            notification_type=Notification.NotificationType.CLAIM_APPROVED
        ).first()
        self.assertIsNotNone(notif_a)

        # Claimant B receives superseded notification
        notif_b = Notification.objects.filter(
            recipient=self.claimant_b,
            notification_type=Notification.NotificationType.CLAIM_SUPERSEDED
        ).first()
        self.assertIsNotNone(notif_b)

        # Audit log created
        audit = AuditLog.objects.filter(
            target_model__iexact='claim',
            target_object_id=str(self.claim_a.pk),
            action_type=AuditLog.ActionType.CLAIM_APPROVED_ADMIN
        ).first()
        self.assertIsNotNone(audit)
        self.assertIn("Claimant provided receipt", audit.reason)


class EmailServiceAndTrackingTest(TestCase):
    """
    Validates email dispatch, user notification preferences,
    and resilience against delivery errors without rolling back DB state.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='email_tester',
            password='Password123!',
            email='tester@findback.local'
        )

    def test_email_sent_successfully_and_tracked(self):
        delivery = send_event_email(
            recipient_user=self.user,
            event_type=EmailDelivery.EventType.ACCOUNT_STATUS_CHANGED,
            context={'reason': 'Periodic security review.'},
            subject='Account Review Notice'
        )
        self.assertIsNotNone(delivery)
        self.assertEqual(delivery.status, EmailDelivery.DeliveryStatus.SENT)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Account Review Notice", mail.outbox[0].subject)

    def test_user_opt_out_preference_respected(self):
        # Disable claim notifications
        profile = self.user.profile
        profile.claim_notifications = False
        profile.save()

        delivery = send_event_email(
            recipient_user=self.user,
            event_type=EmailDelivery.EventType.CLAIM_SUBMITTED,
            context={}
        )
        # Should be skipped
        self.assertIsNone(delivery)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_email_failure_does_not_raise_exception(self):
        # Pass invalid user with broken email or trigger failure
        delivery = send_event_email(
            recipient_user=None,
            event_type=EmailDelivery.EventType.GENERAL_NOTIFICATION
        )
        self.assertIsNone(delivery)


class RealTimeWebSocketTest(TestCase):
    """
    Validates Django Channels WebSocket authentication, group separation,
    and broadcast helpers.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='ws_user',
            password='Password123!',
            email='ws@example.com'
        )
        self.staff_user = User.objects.create_user(
            username='ws_staff',
            password='Password123!',
            email='staff_ws@example.com',
            is_staff=True
        )

    async def test_unauthenticated_websocket_rejected(self):
        from django.contrib.auth.models import AnonymousUser
        communicator = WebsocketCommunicator(LiveUpdatesConsumer.as_asgi(), "/ws/updates/")
        communicator.scope['user'] = AnonymousUser()
        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4001)

    async def test_authenticated_websocket_connected(self):
        communicator = WebsocketCommunicator(LiveUpdatesConsumer.as_asgi(), "/ws/updates/")
        communicator.scope['user'] = self.user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Receive connection confirmation
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'connected')
        self.assertEqual(response['user_id'], self.user.id)
        self.assertFalse(response['is_staff'])

        # Send ping
        await communicator.send_json_to({'type': 'ping'})
        pong = await communicator.receive_json_from()
        self.assertEqual(pong['type'], 'pong')

        await communicator.disconnect()

    def test_broadcast_helpers_execute_safely(self):
        # Test helper functions execute without exception
        publish_user_event(self.user.id, 'test_event', {'message': 'Hello'})
        publish_admin_event('admin_event', {'metric': 42})
