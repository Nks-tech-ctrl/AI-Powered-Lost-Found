from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import IntegrityError
from django.contrib.admin.sites import site

from items.models import Item
from .models import Claim
from .admin import ClaimAdmin


class ClaimModelTest(TestCase):
    """
    Tests for Claim model constraints, fields, string representation, and status defaults.
    """

    def setUp(self):
        self.reporter = User.objects.create_user(
            username='reporter_model',
            email='reporter_m@example.com',
            password='Password123!'
        )
        self.claimant = User.objects.create_user(
            username='claimant_model',
            email='claimant_m@example.com',
            password='Password123!'
        )
        self.item = Item.objects.create(
            user=self.reporter,
            item_type=Item.ItemType.FOUND,
            title='Found Apple Watch Series 8',
            description='Black watch found in gym locker room.',
            category=Item.ItemCategory.WATCH,
            location='Campus Gym',
            date_occurred=timezone.now().date(),
            identification_details='Engraving on back lid: SECRET123',
            status=Item.ItemStatus.ACTIVE
        )

    def test_claim_creation_and_defaults(self):
        """Test 7: Claim starts with PENDING status by default and has a clean __str__."""
        claim = Claim.objects.create(
            item=self.item,
            claimant=self.claimant,
            reason='I lost this exact black watch at the gym yesterday.',
            verification_answer='It has a custom sports band with green stitching.'
        )
        self.assertEqual(claim.status, Claim.Status.PENDING)
        self.assertEqual(str(claim), f"Claim by {self.claimant.username} for {self.item.title}")
        # Ensure __str__ does not expose sensitive verification details
        self.assertNotIn('SECRET123', str(claim))
        self.assertNotIn('custom sports band', str(claim))

    def test_conditional_unique_constraint_prevents_duplicate_pending(self):
        """Test 6: Database constraint prevents duplicate PENDING claims for same user and item."""
        Claim.objects.create(
            item=self.item,
            claimant=self.claimant,
            reason='First claim attempt.',
            status=Claim.Status.PENDING
        )
        with self.assertRaises(IntegrityError):
            Claim.objects.create(
                item=self.item,
                claimant=self.claimant,
                reason='Second pending claim attempt.',
                status=Claim.Status.PENDING
            )

    def test_can_create_claim_after_rejection_or_cancellation(self):
        """Claimant can create a new claim if a previous one was REJECTED or CANCELLED."""
        Claim.objects.create(
            item=self.item,
            claimant=self.claimant,
            reason='First rejected attempt.',
            status=Claim.Status.REJECTED
        )
        # Should succeed because previous claim is REJECTED, not PENDING
        new_claim = Claim.objects.create(
            item=self.item,
            claimant=self.claimant,
            reason='Second claim attempt with more evidence.',
            status=Claim.Status.PENDING
        )
        self.assertEqual(new_claim.status, Claim.Status.PENDING)


class ClaimSubmissionViewTest(TestCase):
    """
    Tests for submitting ownership claims (Rules 1-7).
    """

    def setUp(self):
        self.client = Client()
        self.reporter = User.objects.create_user(
            username='reporter_sub',
            email='reporter_sub@example.com',
            password='Password123!'
        )
        self.claimant = User.objects.create_user(
            username='claimant_sub',
            email='claimant_sub@example.com',
            password='Password123!'
        )
        self.found_item = Item.objects.create(
            user=self.reporter,
            item_type=Item.ItemType.FOUND,
            title='Found Dell XPS 15',
            description='Silver Dell laptop left in library 2nd floor.',
            category=Item.ItemCategory.LAPTOP,
            location='Main Library',
            date_occurred=timezone.now().date(),
            identification_details='Sticker with initials AK under battery',
            status=Item.ItemStatus.ACTIVE
        )
        self.lost_item = Item.objects.create(
            user=self.reporter,
            item_type=Item.ItemType.LOST,
            title='Lost Blue Backpack',
            description='Lost backpack with textbooks.',
            category=Item.ItemCategory.BAG,
            location='Cafeteria',
            date_occurred=timezone.now().date(),
            status=Item.ItemStatus.ACTIVE
        )

    def test_01_anonymous_user_cannot_submit_claim(self):
        """1. Anonymous user cannot submit claim; redirected to login."""
        submit_url = reverse('submit-claim', kwargs={'pk': self.found_item.pk})
        response = self.client.get(submit_url)
        self.assertRedirects(response, f"{reverse('login')}?next={submit_url}")

        post_response = self.client.post(submit_url, {
            'reason': 'This is my laptop and I lost it here.'
        })
        self.assertRedirects(post_response, f"{reverse('login')}?next={submit_url}")
        self.assertEqual(Claim.objects.count(), 0)

    def test_02_authenticated_user_can_submit_valid_claim(self):
        """2. Authenticated user can submit a valid claim."""
        self.client.force_login(self.claimant)
        submit_url = reverse('submit-claim', kwargs={'pk': self.found_item.pk})

        response = self.client.get(submit_url)
        self.assertEqual(response.status_code, 200)

        post_data = {
            'reason': 'I forgot my silver Dell laptop at table 4 near the window.',
            'verification_answer': 'The lock screen wallpaper is a mountain landscape.'
        }
        post_response = self.client.post(submit_url, data=post_data)
        self.assertRedirects(post_response, reverse('my-claims'))

        claim = Claim.objects.get(item=self.found_item, claimant=self.claimant)
        self.assertEqual(claim.status, Claim.Status.PENDING)
        self.assertEqual(claim.reason, post_data['reason'])
        self.assertEqual(claim.verification_answer, post_data['verification_answer'])

    def test_03_user_cannot_claim_their_own_found_item(self):
        """3. User cannot claim their own FOUND item."""
        self.client.force_login(self.reporter)
        submit_url = reverse('submit-claim', kwargs={'pk': self.found_item.pk})

        response = self.client.post(submit_url, {
            'reason': 'Attempting to claim an item I reported myself.'
        })
        self.assertFalse(Claim.objects.filter(claimant=self.reporter).exists())

    def test_04_user_cannot_claim_lost_item(self):
        """4. User cannot claim a LOST item."""
        self.client.force_login(self.claimant)
        submit_url = reverse('submit-claim', kwargs={'pk': self.lost_item.pk})

        response = self.client.post(submit_url, {
            'reason': 'Trying to claim an item that was reported lost.'
        })
        self.assertRedirects(response, reverse('search'))
        self.assertFalse(Claim.objects.filter(item=self.lost_item).exists())

    def test_05_user_cannot_claim_inactive_item(self):
        """5. User cannot claim an inactive item (e.g. CLAIMED, CLOSED)."""
        self.found_item.status = Item.ItemStatus.CLAIMED
        self.found_item.save()

        self.client.force_login(self.claimant)
        submit_url = reverse('submit-claim', kwargs={'pk': self.found_item.pk})

        response = self.client.post(submit_url, {
            'reason': 'Trying to claim an already claimed item.'
        })
        self.assertRedirects(response, reverse('search'))
        self.assertFalse(Claim.objects.filter(claimant=self.claimant).exists())

    def test_06_user_cannot_create_duplicate_pending_claims(self):
        """6. User cannot create duplicate pending claims for the same item."""
        self.client.force_login(self.claimant)
        submit_url = reverse('submit-claim', kwargs={'pk': self.found_item.pk})

        # First claim succeeds
        self.client.post(submit_url, {'reason': 'Initial claim submission reason here.'})
        self.assertEqual(Claim.objects.filter(item=self.found_item, claimant=self.claimant).count(), 1)

        # Second claim attempt
        second_response = self.client.post(submit_url, {'reason': 'Second claim submission attempt.'})
        self.assertRedirects(second_response, reverse('my-claims'))
        self.assertEqual(Claim.objects.filter(item=self.found_item, claimant=self.claimant).count(), 1)


class ClaimDashboardAndReviewWorkflowTest(TestCase):
    """
    Tests for claimant views, reporter review, approval, rejection, and cancellation (Rules 8-18).
    """

    def setUp(self):
        self.client = Client()
        self.reporter = User.objects.create_user(
            username='reporter_rev',
            email='reporter_rev@example.com',
            password='Password123!'
        )
        self.claimant_1 = User.objects.create_user(
            username='claimant_one',
            email='c1@example.com',
            password='Password123!'
        )
        self.claimant_2 = User.objects.create_user(
            username='claimant_two',
            email='c2@example.com',
            password='Password123!'
        )
        self.unrelated_user = User.objects.create_user(
            username='unrelated_user',
            email='unrelated@example.com',
            password='Password123!'
        )

        self.item = Item.objects.create(
            user=self.reporter,
            item_type=Item.ItemType.FOUND,
            title='Found Sony Headphones WH-1000XM4',
            description='Black noise cancelling headphones found on campus bus.',
            category=Item.ItemCategory.ELECTRONICS,
            brand='Sony',
            color='Black',
            location='Campus Shuttle Bus 3',
            date_occurred=timezone.now().date(),
            identification_details='Small dent on left ear cup and blue tape',
            status=Item.ItemStatus.ACTIVE
        )

        self.claim_1 = Claim.objects.create(
            item=self.item,
            claimant=self.claimant_1,
            reason='Left these headphones on the bus yesterday around 4pm.',
            verification_answer='Left cup has blue tape on the slider hinge.',
            status=Claim.Status.PENDING
        )

        self.claim_2 = Claim.objects.create(
            item=self.item,
            claimant=self.claimant_2,
            reason='Lost Sony headphones on bus.',
            verification_answer='No specific marks.',
            status=Claim.Status.PENDING
        )

    def test_08_claimant_can_see_their_own_claim(self):
        """8. Claimant can see their own claim on My Claims page."""
        self.client.force_login(self.claimant_1)
        response = self.client.get(reverse('my-claims'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Found Sony Headphones WH-1000XM4')
        self.assertContains(response, 'Pending')

    def test_09_claimant_cannot_access_another_users_review_page(self):
        """9. Claimant or non-reporter cannot access reporter review page."""
        self.client.force_login(self.claimant_1)
        review_url = reverse('review-claim', kwargs={'pk': self.claim_1.pk})
        response = self.client.get(review_url)
        # Should redirect with error
        self.assertRedirects(response, reverse('claims-to-review'))

    def test_10_reporter_can_review_claims_for_their_own_item(self):
        """10. Reporter can review claims for their own item."""
        self.client.force_login(self.reporter)
        review_url = reverse('review-claim', kwargs={'pk': self.claim_1.pk})
        response = self.client.get(review_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Found Sony Headphones WH-1000XM4')
        self.assertContains(response, self.claimant_1.username)
        self.assertContains(response, 'Left cup has blue tape on the slider hinge.')

    def test_11_reporter_cannot_review_another_users_item_claims(self):
        """11. Reporter cannot review another user's item claims."""
        self.client.force_login(self.unrelated_user)
        review_url = reverse('review-claim', kwargs={'pk': self.claim_1.pk})
        response = self.client.get(review_url)
        self.assertRedirects(response, reverse('claims-to-review'))

    def test_12_and_13_reporter_can_approve_pending_claim_changes_status_to_claimed(self):
        """12 & 13. Reporter can approve pending claim; changes item status to CLAIMED."""
        self.client.force_login(self.reporter)
        approve_url = reverse('approve-claim', kwargs={'pk': self.claim_1.pk})
        response = self.client.post(approve_url)
        self.assertRedirects(response, reverse('review-claim', kwargs={'pk': self.claim_1.pk}))

        self.claim_1.refresh_from_db()
        self.assertEqual(self.claim_1.status, Claim.Status.APPROVED)
        self.assertEqual(self.claim_1.reviewed_by, self.reporter)
        self.assertIsNotNone(self.claim_1.reviewed_at)

        self.item.refresh_from_db()
        self.assertEqual(self.item.status, Item.ItemStatus.CLAIMED)

    def test_14_approval_rejects_other_pending_claims(self):
        """14. Approving one claim automatically and atomically rejects other pending claims."""
        self.client.force_login(self.reporter)
        approve_url = reverse('approve-claim', kwargs={'pk': self.claim_1.pk})
        self.client.post(approve_url)

        self.claim_1.refresh_from_db()
        self.claim_2.refresh_from_db()

        self.assertEqual(self.claim_1.status, Claim.Status.APPROVED)
        self.assertEqual(self.claim_2.status, Claim.Status.REJECTED)
        self.assertIn("Another ownership claim was approved", self.claim_2.reviewer_note)

    def test_15_rejected_claim_leaves_item_active(self):
        """15. Rejected claim sets status REJECTED and leaves item ACTIVE."""
        self.client.force_login(self.reporter)
        reject_url = reverse('reject-claim', kwargs={'pk': self.claim_2.pk})
        response = self.client.post(reject_url, data={'reviewer_note': 'Serial number does not match.'})
        self.assertRedirects(response, reverse('review-claim', kwargs={'pk': self.claim_2.pk}))

        self.claim_2.refresh_from_db()
        self.assertEqual(self.claim_2.status, Claim.Status.REJECTED)
        self.assertEqual(self.claim_2.reviewer_note, 'Serial number does not match.')

        self.item.refresh_from_db()
        self.assertEqual(self.item.status, Item.ItemStatus.ACTIVE)

    def test_16_claimant_can_cancel_pending_claim(self):
        """16. Claimant can cancel their own PENDING claim."""
        self.client.force_login(self.claimant_1)
        cancel_url = reverse('cancel-claim', kwargs={'pk': self.claim_1.pk})
        response = self.client.post(cancel_url)
        self.assertRedirects(response, reverse('my-claims'))

        self.claim_1.refresh_from_db()
        self.assertEqual(self.claim_1.status, Claim.Status.CANCELLED)

    def test_17_claimant_cannot_cancel_approved_claim(self):
        """17. Claimant cannot cancel an APPROVED claim."""
        self.claim_1.status = Claim.Status.APPROVED
        self.claim_1.save()

        self.client.force_login(self.claimant_1)
        cancel_url = reverse('cancel-claim', kwargs={'pk': self.claim_1.pk})
        response = self.client.post(cancel_url)
        self.assertRedirects(response, reverse('my-claims'))

        self.claim_1.refresh_from_db()
        self.assertEqual(self.claim_1.status, Claim.Status.APPROVED)

    def test_18_get_requests_cannot_approve_reject_or_cancel_claims(self):
        """18. GET requests cannot approve, reject, or cancel claims."""
        self.client.force_login(self.reporter)

        # GET to approve
        approve_url = reverse('approve-claim', kwargs={'pk': self.claim_1.pk})
        get_approve = self.client.get(approve_url)
        self.claim_1.refresh_from_db()
        self.assertEqual(self.claim_1.status, Claim.Status.PENDING)

        # GET to reject
        reject_url = reverse('reject-claim', kwargs={'pk': self.claim_1.pk})
        get_reject = self.client.get(reject_url)
        self.claim_1.refresh_from_db()
        self.assertEqual(self.claim_1.status, Claim.Status.PENDING)

        # GET to cancel
        self.client.force_login(self.claimant_1)
        cancel_url = reverse('cancel-claim', kwargs={'pk': self.claim_1.pk})
        get_cancel = self.client.get(cancel_url)
        self.claim_1.refresh_from_db()
        self.assertEqual(self.claim_1.status, Claim.Status.PENDING)


class SecurityPrivacyAndAdminTest(TestCase):
    """
    Tests for CSRF enforcement, privacy safeguards, and admin registration (Rules 19-20, 17, 15).
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='privacy_user',
            email='privacy@example.com',
            password='Password123!'
        )
        self.item = Item.objects.create(
            user=self.user,
            item_type=Item.ItemType.FOUND,
            title='Found iPhone 15 Pro Titanium',
            description='Natural titanium iPhone 15 Pro found on library study table.',
            category=Item.ItemCategory.MOBILE,
            location='Library 3rd Floor',
            date_occurred=timezone.now().date(),
            identification_details='IMEI: 352098001234567, lockscreen is a golden retriever named Max',
            status=Item.ItemStatus.ACTIVE
        )

    def test_19_csrf_protection_remains_enabled(self):
        """19. CSRF protection remains active on submission POST."""
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        other_item = Item.objects.create(
            user=User.objects.create_user(username='other_rep', password='Password123!'),
            item_type=Item.ItemType.FOUND,
            title='Keys',
            category=Item.ItemCategory.KEYS,
            location='Lobby',
            date_occurred=timezone.now().date(),
            status=Item.ItemStatus.ACTIVE
        )
        # Attempt POST without CSRF token
        submit_url = reverse('submit-claim', kwargs={'pk': other_item.pk})
        response = csrf_client.post(submit_url, {'reason': 'My keys left on table.'})
        self.assertEqual(response.status_code, 403)

    def test_20_private_identification_details_never_appear_on_public_pages(self):
        """20. Private identification_details never appear on public item detail or catalog pages."""
        public_url = reverse('public-item-detail', kwargs={'pk': self.item.pk})
        response = self.client.get(public_url)
        self.assertEqual(response.status_code, 200)

        # Verify public metadata appears
        self.assertContains(response, 'Found iPhone 15 Pro Titanium')
        self.assertContains(response, 'Library 3rd Floor')

        # Strictly verify private identification details DO NOT appear
        self.assertNotContains(response, '352098001234567')
        self.assertNotContains(response, 'golden retriever named Max')
        self.assertNotContains(response, 'privacy@example.com')

    def test_claims_admin_registered(self):
        """17. Claim model is registered in Django admin with correct configuration."""
        self.assertIn(Claim, site._registry)
        model_admin = site._registry[Claim]
        self.assertIsInstance(model_admin, ClaimAdmin)
        self.assertIn('item', model_admin.list_display)
        self.assertIn('claimant', model_admin.list_display)
        self.assertIn('status', model_admin.list_display)
        self.assertIn('status', model_admin.list_filter)
        self.assertIn('created_at', model_admin.readonly_fields)

    def test_dashboard_displays_real_claims_metrics(self):
        """15. Dashboard displays real database claims metrics and quick actions."""
        claimant = User.objects.create_user(username='dash_claimant', password='Password123!')
        Claim.objects.create(
            item=self.item,
            claimant=claimant,
            reason='Claim on user item.',
            status=Claim.Status.PENDING
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Claims to Review')
        self.assertContains(response, 'My Claims')
        self.assertEqual(response.context['claims_to_review_pending'], 1)
        self.assertEqual(response.context['my_claims_pending'], 0)


class AdminClaimApprovalWorkflowTest(TestCase):
    """
    Tests for staff/admin claim moderation and approval directly from the website (frontend).
    """

    def setUp(self):
        self.client = Client()
        self.staff_admin = User.objects.create_user(
            username='staff_admin',
            email='admin@example.com',
            password='Password123!',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='regular_member',
            email='member@example.com',
            password='Password123!',
            is_staff=False
        )
        self.reporter = User.objects.create_user(
            username='finder_reporter',
            email='finder@example.com',
            password='Password123!'
        )
        self.claimant_1 = User.objects.create_user(
            username='claimant_first',
            email='claimant1@example.com',
            password='Password123!'
        )
        self.claimant_2 = User.objects.create_user(
            username='claimant_second',
            email='claimant2@example.com',
            password='Password123!'
        )

        self.found_item = Item.objects.create(
            user=self.reporter,
            item_type=Item.ItemType.FOUND,
            title='Found MacBook Pro 16-inch Space Black',
            description='Found at the campus coffee shop.',
            category=Item.ItemCategory.LAPTOP,
            location='Campus Coffee Shop',
            date_occurred=timezone.now().date(),
            identification_details='Serial: C02X1234TEST; sticker of Linux penguin on bottom right',
            status=Item.ItemStatus.ACTIVE
        )

        self.claim_1 = Claim.objects.create(
            item=self.found_item,
            claimant=self.claimant_1,
            reason='I left my laptop at the table next to the window while ordering.',
            verification_answer='It has a Linux penguin sticker on the bottom casing.',
            status=Claim.Status.PENDING
        )

        self.claim_2 = Claim.objects.create(
            item=self.found_item,
            claimant=self.claimant_2,
            reason='Lost similar macbook.',
            status=Claim.Status.PENDING
        )

    def test_admin_claims_list_requires_staff_access(self):
        """Anonymous and regular users cannot access the admin claims moderation queue."""
        admin_url = reverse('admin-claims')

        # Anonymous user -> redirected to login
        response = self.client.get(admin_url)
        self.assertRedirects(response, f"{reverse('login')}?next={admin_url}")

        # Regular user -> redirected to dashboard with error
        self.client.force_login(self.regular_user)
        response_user = self.client.get(admin_url)
        self.assertRedirects(response_user, reverse('dashboard'))

    def test_staff_can_view_all_claims_in_admin_list(self):
        """Staff user can view all platform claims, search, and filter by status on the website."""
        self.client.force_login(self.staff_admin)
        response = self.client.get(reverse('admin-claims'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Platform Claims Administration')
        self.assertContains(response, 'Found MacBook Pro 16-inch Space Black')
        self.assertContains(response, 'claimant_first')
        self.assertContains(response, 'finder_reporter')

        # Test status filter
        filter_resp = self.client.get(reverse('admin-claims') + '?status=pending')
        self.assertEqual(filter_resp.status_code, 200)
        self.assertEqual(len(filter_resp.context['claims']), 2)

        # Test search query
        search_resp = self.client.get(reverse('admin-claims') + '?q=MacBook')
        self.assertEqual(search_resp.status_code, 200)
        self.assertEqual(len(search_resp.context['claims']), 2)

    def test_staff_can_open_review_page_with_admin_privileges(self):
        """Staff can open claim review page for any item and inspect private verification clues."""
        self.client.force_login(self.staff_admin)
        review_url = reverse('review-claim', kwargs={'pk': self.claim_1.pk})
        response = self.client.get(review_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_admin_reviewer'])
        self.assertContains(response, 'Administrator Moderation Mode')
        # Admin can see private verification reference
        self.assertContains(response, 'C02X1234TEST')
        self.assertContains(response, 'Linux penguin on bottom right')

    def test_staff_can_approve_claim_from_website(self):
        """Staff can approve a pending claim on the website: item becomes CLAIMED, other claims REJECTED."""
        self.client.force_login(self.staff_admin)
        approve_url = reverse('approve-claim', kwargs={'pk': self.claim_1.pk})
        response = self.client.post(approve_url)
        self.assertRedirects(response, reverse('review-claim', kwargs={'pk': self.claim_1.pk}))

        self.claim_1.refresh_from_db()
        self.claim_2.refresh_from_db()
        self.found_item.refresh_from_db()

        self.assertEqual(self.claim_1.status, Claim.Status.APPROVED)
        self.assertEqual(self.claim_1.reviewed_by, self.staff_admin)
        self.assertEqual(self.found_item.status, Item.ItemStatus.CLAIMED)

        # Competing pending claim is atomically rejected with admin notice
        self.assertEqual(self.claim_2.status, Claim.Status.REJECTED)
        self.assertIn('administration', self.claim_2.reviewer_note.lower())

    def test_staff_can_reject_claim_from_website(self):
        """Staff can reject a pending claim on the website: claim becomes REJECTED, item remains ACTIVE."""
        self.client.force_login(self.staff_admin)
        reject_url = reverse('reject-claim', kwargs={'pk': self.claim_2.pk})
        response = self.client.post(reject_url, data={'reviewer_note': 'Verification answers do not match.'})
        self.assertRedirects(response, reverse('review-claim', kwargs={'pk': self.claim_2.pk}))

        self.claim_2.refresh_from_db()
        self.found_item.refresh_from_db()

        self.assertEqual(self.claim_2.status, Claim.Status.REJECTED)
        self.assertEqual(self.claim_2.reviewed_by, self.staff_admin)
        self.assertEqual(self.claim_2.reviewer_note, 'Verification answers do not match.')
        self.assertEqual(self.found_item.status, Item.ItemStatus.ACTIVE)

    def test_context_processor_admin_pending_badge_count(self):
        """Context processor calculates admin_pending_claims_count for staff users."""
        self.client.force_login(self.staff_admin)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admin_pending_claims_count'], 2)

        self.client.force_login(self.regular_user)
        response_reg = self.client.get(reverse('dashboard'))
        self.assertEqual(response_reg.context['admin_pending_claims_count'], 0)

