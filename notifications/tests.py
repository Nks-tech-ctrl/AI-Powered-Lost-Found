from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.admin.sites import site

from items.models import Item
from claims.models import Claim
from notifications.models import Notification
from notifications.services import create_notification
from notifications.admin import NotificationAdmin


class NotificationModelAndServiceTest(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username='user_a', password='password123', email='a@example.com')
        self.user_b = User.objects.create_user(username='user_b', password='password123', email='b@example.com')
        self.item = Item.objects.create(
            user=self.user_a,
            item_type=Item.ItemType.FOUND,
            title='Keys Found in Park',
            description='Set of brass keys with blue keychain',
            category=Item.ItemCategory.KEYS,
            location='Central Park',
            date_occurred=timezone.now().date(),
        )

    def test_notification_creation_and_defaults(self):
        """Test creating a Notification model record directly."""
        notif = Notification.objects.create(
            recipient=self.user_a,
            notification_type=Notification.NotificationType.CLAIM_SUBMITTED,
            title='New Claim Received',
            message='Someone claimed your found keys.',
            item=self.item
        )
        self.assertFalse(notif.is_read)
        self.assertIsNone(notif.read_at)
        self.assertIn('Notification for user_a', str(notif))

    def test_mark_as_read_method(self):
        """Test mark_as_read() helper updates is_read and read_at."""
        notif = Notification.objects.create(
            recipient=self.user_a,
            notification_type=Notification.NotificationType.CLAIM_APPROVED,
            title='Claim Approved',
            message='Your claim was approved.',
        )
        self.assertFalse(notif.is_read)
        notif.mark_as_read()
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)
        self.assertIsNotNone(notif.read_at)

    def test_create_notification_service(self):
        """Test create_notification service creates valid database record."""
        notif = create_notification(
            recipient=self.user_b,
            notification_type=Notification.NotificationType.CLAIM_APPROVED,
            title='Approval Notice',
            message='Your claim has been accepted.',
            item=self.item
        )
        self.assertIsNotNone(notif)
        self.assertEqual(notif.recipient, self.user_b)
        self.assertEqual(notif.notification_type, Notification.NotificationType.CLAIM_APPROVED)
        self.assertEqual(Notification.objects.filter(recipient=self.user_b).count(), 1)

    def test_create_notification_with_invalid_recipient_fails_safely(self):
        """Test create_notification handles None or invalid recipient safely without crashing."""
        notif = create_notification(
            recipient=None,
            notification_type=Notification.NotificationType.CLAIM_SUBMITTED,
            title='Invalid Test',
            message='Test with no recipient'
        )
        self.assertIsNone(notif)

    def test_admin_registered(self):
        """Verify Notification is registered in Django admin with NotificationAdmin."""
        self.assertIn(Notification, site._registry)
        model_admin = site._registry[Notification]
        self.assertIsInstance(model_admin, NotificationAdmin)
        self.assertIn('recipient', model_admin.list_display)
        self.assertIn('notification_type', model_admin.list_display)


class NotificationViewsAndPermissionsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.alice = User.objects.create_user(username='alice', password='Password123!', email='alice@example.com')
        self.bob = User.objects.create_user(username='bob', password='Password123!', email='bob@example.com')

        # Create notifications for Alice
        self.notif_alice_1 = Notification.objects.create(
            recipient=self.alice,
            notification_type=Notification.NotificationType.CLAIM_SUBMITTED,
            title='Alice Alert 1',
            message='Message for Alice 1',
            is_read=False
        )
        self.notif_alice_2 = Notification.objects.create(
            recipient=self.alice,
            notification_type=Notification.NotificationType.CLAIM_APPROVED,
            title='Alice Alert 2',
            message='Message for Alice 2',
            is_read=True,
            read_at=timezone.now()
        )

        # Create notification for Bob
        self.notif_bob = Notification.objects.create(
            recipient=self.bob,
            notification_type=Notification.NotificationType.CLAIM_REJECTED,
            title='Bob Alert',
            message='Message for Bob',
            is_read=False
        )

    def test_anonymous_user_redirected_to_login(self):
        """Anonymous users must be redirected to login when visiting /notifications/."""
        response = self.client.get(reverse('notifications'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('notifications')}")

    def test_notifications_list_shows_only_current_user_records(self):
        """User Alice can only see her notifications, not Bob's."""
        self.client.force_login(self.alice)
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alice Alert 1')
        self.assertContains(response, 'Alice Alert 2')
        self.assertNotContains(response, 'Bob Alert')

    def test_notifications_filter_unread_and_read(self):
        """Filter by ?status=unread and ?status=read displays correct items."""
        self.client.force_login(self.alice)

        # Unread filter
        resp_unread = self.client.get(reverse('notifications') + '?status=unread')
        self.assertEqual(resp_unread.status_code, 200)
        self.assertContains(resp_unread, 'Alice Alert 1')
        self.assertNotContains(resp_unread, 'Alice Alert 2')

        # Read filter
        resp_read = self.client.get(reverse('notifications') + '?status=read')
        self.assertEqual(resp_read.status_code, 200)
        self.assertNotContains(resp_read, 'Alice Alert 1')
        self.assertContains(resp_read, 'Alice Alert 2')

    def test_mark_single_notification_read_post_only(self):
        """Marking a notification as read requires POST and marks the record."""
        self.client.force_login(self.alice)

        # GET is rejected
        resp_get = self.client.get(reverse('notification-read', kwargs={'pk': self.notif_alice_1.pk}))
        self.assertRedirects(resp_get, reverse('notifications'))
        self.notif_alice_1.refresh_from_db()
        self.assertFalse(self.notif_alice_1.is_read)

        # POST succeeds
        resp_post = self.client.post(reverse('notification-read', kwargs={'pk': self.notif_alice_1.pk}))
        self.assertRedirects(resp_post, reverse('notifications'))
        self.notif_alice_1.refresh_from_db()
        self.assertTrue(self.notif_alice_1.is_read)
        self.assertIsNotNone(self.notif_alice_1.read_at)

    def test_mark_single_notification_read_idor_protection(self):
        """Bob cannot mark Alice's notification as read (returns 404)."""
        self.client.force_login(self.bob)
        response = self.client.post(reverse('notification-read', kwargs={'pk': self.notif_alice_1.pk}))
        self.assertEqual(response.status_code, 404)
        self.notif_alice_1.refresh_from_db()
        self.assertFalse(self.notif_alice_1.is_read)

    def test_mark_all_read_updates_only_current_user_unread(self):
        """Mark-all-read updates all unread notifications for current user, without touching others."""
        self.client.force_login(self.alice)
        response = self.client.post(reverse('notifications-read-all'))
        self.assertRedirects(response, reverse('notifications'))

        self.notif_alice_1.refresh_from_db()
        self.assertTrue(self.notif_alice_1.is_read)

        # Bob's notification remains unread
        self.notif_bob.refresh_from_db()
        self.assertFalse(self.notif_bob.is_read)

    def test_delete_notification_post_only(self):
        """Deleting notification requires POST and removes only owner's notification."""
        self.client.force_login(self.alice)

        # GET is rejected
        resp_get = self.client.get(reverse('notification-delete', kwargs={'pk': self.notif_alice_1.pk}))
        self.assertRedirects(resp_get, reverse('notifications'))
        self.assertTrue(Notification.objects.filter(pk=self.notif_alice_1.pk).exists())

        # POST deletes
        resp_post = self.client.post(reverse('notification-delete', kwargs={'pk': self.notif_alice_1.pk}))
        self.assertRedirects(resp_post, reverse('notifications'))
        self.assertFalse(Notification.objects.filter(pk=self.notif_alice_1.pk).exists())

    def test_delete_notification_idor_protection(self):
        """Bob cannot delete Alice's notification (returns 404)."""
        self.client.force_login(self.bob)
        response = self.client.post(reverse('notification-delete', kwargs={'pk': self.notif_alice_2.pk}))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Notification.objects.filter(pk=self.notif_alice_2.pk).exists())

    def test_context_processor_counts(self):
        """Context processor returns accurate unread count for user and 0 for anonymous."""
        # Authenticated user Alice (1 unread)
        self.client.force_login(self.alice)
        resp_auth = self.client.get(reverse('dashboard'))
        self.assertEqual(resp_auth.context['unread_notifications_count'], 1)

        # Anonymous user (0 unread)
        self.client.logout()
        resp_anon = self.client.get(reverse('home'))
        self.assertEqual(resp_anon.context['unread_notifications_count'], 0)


class ClaimsWorkflowNotificationIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.reporter = User.objects.create_user(username='reporter', password='Password123!', email='rep@example.com')
        self.claimant_1 = User.objects.create_user(username='claimant1', password='Password123!', email='c1@example.com')
        self.claimant_2 = User.objects.create_user(username='claimant2', password='Password123!', email='c2@example.com')

        self.item = Item.objects.create(
            user=self.reporter,
            item_type=Item.ItemType.FOUND,
            title='Found Silver iPhone 14',
            description='Silver iPhone with clear case found at Food Court.',
            category=Item.ItemCategory.MOBILE,
            location='Food Court',
            date_occurred=timezone.now().date(),
            status=Item.ItemStatus.ACTIVE,
            identification_details='Lock screen wallpaper of a golden retriever'
        )

    def test_claim_submission_notifies_reporter(self):
        """Submitting a claim triggers CLAIM_SUBMITTED notification for item reporter."""
        self.client.force_login(self.claimant_1)
        post_data = {
            'reason': 'I lost my silver iPhone 14 at the food court around lunchtime.',
            'verification_answer': 'The lock screen shows a golden retriever named Max.'
        }
        response = self.client.post(reverse('submit-claim', kwargs={'pk': self.item.pk}), data=post_data)
        self.assertRedirects(response, reverse('my-claims'))

        # Verify reporter received notification
        notif = Notification.objects.filter(recipient=self.reporter).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.notification_type, Notification.NotificationType.CLAIM_SUBMITTED)
        self.assertIn("Found Silver iPhone 14", notif.message)
        # Ensure private verification answer is not leaked in notification message
        self.assertNotIn("golden retriever named Max", notif.message)

    def test_claim_cancellation_notifies_reporter(self):
        """Cancelling a pending claim triggers CLAIM_CANCELLED notification for reporter."""
        claim = Claim.objects.create(
            item=self.item,
            claimant=self.claimant_1,
            reason='My phone',
            status=Claim.Status.PENDING
        )
        self.client.force_login(self.claimant_1)
        response = self.client.post(reverse('cancel-claim', kwargs={'pk': claim.pk}))
        self.assertRedirects(response, reverse('my-claims'))

        notif = Notification.objects.filter(recipient=self.reporter, notification_type=Notification.NotificationType.CLAIM_CANCELLED).first()
        self.assertIsNotNone(notif)
        self.assertIn("cancelled", notif.message.lower())

    def test_claim_rejection_notifies_claimant(self):
        """Rejecting a pending claim triggers CLAIM_REJECTED notification for claimant."""
        claim = Claim.objects.create(
            item=self.item,
            claimant=self.claimant_1,
            reason='My phone',
            status=Claim.Status.PENDING
        )
        self.client.force_login(self.reporter)
        response = self.client.post(
            reverse('reject-claim', kwargs={'pk': claim.pk}),
            data={'reviewer_note': 'The lock screen description did not match.'}
        )
        self.assertRedirects(response, reverse('review-claim', kwargs={'pk': claim.pk}))

        notif = Notification.objects.filter(recipient=self.claimant_1).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.notification_type, Notification.NotificationType.CLAIM_REJECTED)
        self.assertIn("did not match", notif.message)

    def test_claim_approval_notifies_claimant_and_supersedes_other_pending(self):
        """
        Approving claim triggers:
        - CLAIM_APPROVED notification to approved claimant
        - CLAIM_SUPERSEDED notification to other pending claimants
        - Item status changes to CLAIMED
        """
        claim_1 = Claim.objects.create(
            item=self.item,
            claimant=self.claimant_1,
            reason='My phone claim 1',
            status=Claim.Status.PENDING
        )
        claim_2 = Claim.objects.create(
            item=self.item,
            claimant=self.claimant_2,
            reason='My phone claim 2',
            status=Claim.Status.PENDING
        )

        self.client.force_login(self.reporter)
        response = self.client.post(reverse('approve-claim', kwargs={'pk': claim_1.pk}))
        self.assertRedirects(response, reverse('review-claim', kwargs={'pk': claim_1.pk}))

        # 1. Check item is CLAIMED
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, Item.ItemStatus.CLAIMED)

        # 2. Check claim 1 approved notification
        notif_1 = Notification.objects.filter(recipient=self.claimant_1).first()
        self.assertIsNotNone(notif_1)
        self.assertEqual(notif_1.notification_type, Notification.NotificationType.CLAIM_APPROVED)

        # 3. Check claim 2 superseded notification
        notif_2 = Notification.objects.filter(recipient=self.claimant_2).first()
        self.assertIsNotNone(notif_2)
        self.assertEqual(notif_2.notification_type, Notification.NotificationType.CLAIM_SUPERSEDED)
        # Identity of claimant_1 should not be leaked in claimant_2's notification
        self.assertNotIn("claimant1", notif_2.message)
