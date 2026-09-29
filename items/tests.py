import datetime
import io
from PIL import Image as PILImage
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.admin.sites import site
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from .models import Item
from .forms import ItemForm
from .admin import ItemAdmin


def create_test_image():
    """Helper to generate a minimal valid in-memory JPEG image."""
    file_obj = io.BytesIO()
    image = PILImage.new("RGB", (100, 100), color=(73, 109, 137))
    image.save(file_obj, format="JPEG")
    file_obj.seek(0)
    return SimpleUploadedFile("test_item.jpg", file_obj.read(), content_type="image/jpeg")


class ItemModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword123',
            email='testuser@example.com'
        )

    def test_create_lost_item(self):
        """Test creating a LOST item report successfully."""
        item = Item.objects.create(
            user=self.user,
            item_type=Item.ItemType.LOST,
            title='Black Backpack',
            description='Black backpack with two compartments.',
            category=Item.ItemCategory.BAG,
            brand='Wildcraft',
            color='Black',
            location='College Library',
            date_occurred=timezone.now().date(),
            identification_details='Small scratch near zipper.'
        )
        self.assertEqual(item.title, 'Black Backpack')
        self.assertEqual(item.item_type, Item.ItemType.LOST)
        self.assertEqual(item.status, Item.ItemStatus.ACTIVE)
        self.assertEqual(str(item), 'Black Backpack')
        self.assertEqual(self.user.items.count(), 1)
        self.assertEqual(self.user.items.first(), item)

    def test_create_found_item(self):
        """Test creating a FOUND item report successfully."""
        item = Item.objects.create(
            user=self.user,
            item_type=Item.ItemType.FOUND,
            title='Silver Watch',
            description='Found silver analog watch near the water cooler.',
            category=Item.ItemCategory.WATCH,
            brand='Titan',
            color='Silver',
            location='Vaish College Campus',
            date_occurred=timezone.now().date(),
        )
        self.assertEqual(item.title, 'Silver Watch')
        self.assertEqual(item.item_type, Item.ItemType.FOUND)
        self.assertEqual(item.status, Item.ItemStatus.ACTIVE)

    def test_user_cascade_deletion(self):
        """Test that deleting a user deletes their item reports."""
        Item.objects.create(
            user=self.user,
            item_type=Item.ItemType.LOST,
            title='Keys',
            description='Set of keys with blue keychain',
            category=Item.ItemCategory.KEYS,
            location='Bus Stand',
            date_occurred=timezone.now().date(),
        )
        self.assertEqual(Item.objects.count(), 1)
        self.user.delete()
        self.assertEqual(Item.objects.count(), 0)

    def test_future_date_validation_clean(self):
        """Test that a date in the future raises a ValidationError with expected message."""
        tomorrow = timezone.now().date() + datetime.timedelta(days=1)
        item = Item(
            user=self.user,
            item_type=Item.ItemType.LOST,
            title='Future Lost Item',
            description='Lost tomorrow',
            category=Item.ItemCategory.OTHER,
            location='Future Plaza',
            date_occurred=tomorrow,
        )
        with self.assertRaises(ValidationError) as context:
            item.full_clean()
        
        self.assertIn('The lost/found date cannot be in the future.', str(context.exception))

    def test_past_date_validation_succeeds(self):
        """Test that a date in the past validates successfully."""
        past_date = timezone.now().date() - datetime.timedelta(days=5)
        item = Item(
            user=self.user,
            item_type=Item.ItemType.LOST,
            title='Past Lost Item',
            description='Lost last week',
            category=Item.ItemCategory.MOBILE,
            location='Railway Station',
            date_occurred=past_date,
        )
        item.full_clean()
        item.save()
        self.assertEqual(Item.objects.count(), 1)

    def test_ordering_newest_first(self):
        """Test that items are ordered with newest reports first."""
        item1 = Item.objects.create(
            user=self.user,
            item_type=Item.ItemType.LOST,
            title='First Item',
            description='First description',
            category=Item.ItemCategory.BOOK,
            location='Library',
            date_occurred=timezone.now().date(),
        )
        item2 = Item.objects.create(
            user=self.user,
            item_type=Item.ItemType.FOUND,
            title='Second Item',
            description='Second description',
            category=Item.ItemCategory.OTHER,
            location='Cafeteria',
            date_occurred=timezone.now().date(),
        )
        items = list(Item.objects.all())
        self.assertEqual(items[0], item2)
        self.assertEqual(items[1], item1)


class ItemFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='formuser',
            password='formpassword123'
        )

    def test_form_valid_data(self):
        """Test ItemForm with valid data."""
        form_data = {
            'title': 'Blue Denim Jacket',
            'description': 'Left on chair in seminar hall.',
            'category': Item.ItemCategory.CLOTHING,
            'brand': 'Levi\'s',
            'color': 'Blue',
            'location': 'Seminar Hall A',
            'date_occurred': timezone.now().date().isoformat(),
            'identification_details': 'Name written on collar tag.',
        }
        form = ItemForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        item = form.save(commit=False)
        item.user = self.user
        item.item_type = Item.ItemType.LOST
        item.status = Item.ItemStatus.ACTIVE
        item.save()
        self.assertEqual(item.item_type, Item.ItemType.LOST)
        self.assertEqual(item.status, Item.ItemStatus.ACTIVE)
        self.assertEqual(item.title, 'Blue Denim Jacket')

    def test_form_future_date_fails(self):
        """Test that form rejects future dates with friendly message."""
        tomorrow = timezone.now().date() + datetime.timedelta(days=2)
        form_data = {
            'title': 'Test Item',
            'description': 'Valid description',
            'category': Item.ItemCategory.ELECTRONICS,
            'location': 'Auditorium',
            'date_occurred': tomorrow.isoformat(),
        }
        form = ItemForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('date_occurred', form.errors)
        self.assertIn('The lost/found date cannot be in the future.', form.errors['date_occurred'])

    def test_form_does_not_expose_restricted_fields(self):
        """Test that user, item_type, status, created_at, updated_at are not editable fields in the form."""
        form = ItemForm()
        self.assertNotIn('user', form.fields)
        self.assertNotIn('item_type', form.fields)
        self.assertNotIn('status', form.fields)
        self.assertNotIn('created_at', form.fields)
        self.assertNotIn('updated_at', form.fields)


class ItemAdminTest(TestCase):
    def test_admin_registered(self):
        """Test that Item is registered in Django admin with ItemAdmin."""
        self.assertIn(Item, site._registry)
        model_admin = site._registry[Item]
        self.assertIsInstance(model_admin, ItemAdmin)
        self.assertIn('title', model_admin.list_display)
        self.assertIn('user', model_admin.list_display)
        self.assertIn('item_type', model_admin.list_display)
        self.assertIn('status', model_admin.list_display)
        self.assertIn('item_type', model_admin.list_filter)
        self.assertIn('title', model_admin.search_fields)
        self.assertNotIn('identification_details', model_admin.list_display)


class ReportViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(
            username='user_a',
            email='user_a@example.com',
            password='Password123!'
        )
        self.user_b = User.objects.create_user(
            username='user_b',
            email='user_b@example.com',
            password='Password123!'
        )

    def test_unauthenticated_user_redirected_to_login(self):
        """Test unauthenticated users cannot access report pages directly."""
        resp_lost = self.client.get(reverse('report-lost'))
        self.assertRedirects(resp_lost, f"{reverse('login')}?next={reverse('report-lost')}")

        resp_found = self.client.get(reverse('report-found'))
        self.assertRedirects(resp_found, f"{reverse('login')}?next={reverse('report-found')}")

    def test_report_lost_get_renders_form(self):
        """Test authenticated user GET on report-lost renders empty form."""
        self.client.force_login(self.user_a)
        response = self.client.get(reverse('report-lost'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'items/report-lost.html')
        self.assertIn('form', response.context)
        self.assertEqual(response.context['report_type'], 'lost')

    def test_report_lost_post_success(self):
        """Test authenticated user submitting a valid lost report."""
        self.client.force_login(self.user_a)
        today = timezone.now().date()
        post_data = {
            'title': 'Black Backpack',
            'category': Item.ItemCategory.BAG,
            'brand': 'Wildcraft',
            'color': 'Black',
            'location': 'College Library',
            'date_occurred': today.isoformat(),
            'description': 'Black backpack with two compartments.',
            'identification_details': 'Small scratch near zipper.'
        }
        response = self.client.post(reverse('report-lost'), data=post_data)
        self.assertRedirects(response, reverse('dashboard'))

        # Verify database record
        item = Item.objects.get(title='Black Backpack')
        self.assertEqual(item.user, self.user_a)
        self.assertEqual(item.item_type, Item.ItemType.LOST)
        self.assertEqual(item.status, Item.ItemStatus.ACTIVE)
        self.assertEqual(item.brand, 'Wildcraft')
        self.assertEqual(item.location, 'College Library')
        self.assertEqual(item.identification_details, 'Small scratch near zipper.')

        # Verify success message
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Your lost item report has been submitted successfully." in m.message for m in messages_list))

    def test_report_found_post_success(self):
        """Test authenticated user submitting a valid found report."""
        self.client.force_login(self.user_b)
        today = timezone.now().date()
        post_data = {
            'title': 'Silver Watch',
            'category': Item.ItemCategory.WATCH,
            'brand': 'Casio',
            'color': 'Silver',
            'location': 'College Campus',
            'date_occurred': today.isoformat(),
            'description': 'Silver wrist watch found near the library entrance.',
            'identification_details': 'Engraving on back case.'
        }
        response = self.client.post(reverse('report-found'), data=post_data)
        self.assertRedirects(response, reverse('dashboard'))

        # Verify database record
        item = Item.objects.get(title='Silver Watch')
        self.assertEqual(item.user, self.user_b)
        self.assertEqual(item.item_type, Item.ItemType.FOUND)
        self.assertEqual(item.status, Item.ItemStatus.ACTIVE)
        self.assertEqual(item.brand, 'Casio')
        self.assertEqual(item.location, 'College Campus')

        # Verify success message
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Your found item report has been submitted successfully." in m.message for m in messages_list))

    def test_server_enforces_user_and_type_security(self):
        """Test that user cannot spoof ownership or item_type via client POST data."""
        self.client.force_login(self.user_a)
        today = timezone.now().date()
        malicious_data = {
            'user': self.user_b.id,
            'item_type': 'FOUND',
            'status': 'CLAIMED',
            'title': 'Spoofed Report',
            'category': Item.ItemCategory.ELECTRONICS,
            'location': 'Main Gate',
            'date_occurred': today.isoformat(),
            'description': 'Attempting to inject user and status',
        }
        response = self.client.post(reverse('report-lost'), data=malicious_data)
        self.assertRedirects(response, reverse('dashboard'))

        item = Item.objects.get(title='Spoofed Report')
        # Server must assign user_a (logged-in), LOST (endpoint), and ACTIVE (default)
        self.assertEqual(item.user, self.user_a)
        self.assertEqual(item.item_type, Item.ItemType.LOST)
        self.assertEqual(item.status, Item.ItemStatus.ACTIVE)

    def test_future_date_fails_and_preserves_data(self):
        """Test that entering a future date fails and preserves input values."""
        self.client.force_login(self.user_a)
        tomorrow = timezone.now().date() + datetime.timedelta(days=1)
        post_data = {
            'title': 'Future Report',
            'category': Item.ItemCategory.OTHER,
            'location': 'Test Location',
            'date_occurred': tomorrow.isoformat(),
            'description': 'Lost tomorrow',
        }
        response = self.client.post(reverse('report-lost'), data=post_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Item.objects.filter(title='Future Report').exists())
        self.assertFormError(response.context['form'], 'date_occurred', 'The lost/found date cannot be in the future.')
        self.assertContains(response, 'Future Report')

    def test_missing_required_fields_fails(self):
        """Test that submitting with missing required fields fails validation."""
        self.client.force_login(self.user_a)
        post_data = {
            'title': 'Incomplete Report',
            # missing category, location, date_occurred, description
        }
        response = self.client.post(reverse('report-lost'), data=post_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Item.objects.filter(title='Incomplete Report').exists())
        self.assertFormError(response.context['form'], 'category', 'Please select a category.')
        self.assertFormError(response.context['form'], 'description', 'Please provide a detailed description of the item.')
        self.assertFormError(response.context['form'], 'location', 'Please enter the location where the item was lost or found.')

    def test_image_upload_success(self):
        """Test uploading a photograph with a report successfully saves the file."""
        self.client.force_login(self.user_a)
        test_img = create_test_image()
        today = timezone.now().date()
        post_data = {
            'title': 'Item with Photo',
            'category': Item.ItemCategory.ELECTRONICS,
            'location': 'Lab 3',
            'date_occurred': today.isoformat(),
            'description': 'Item with real image file',
            'image': test_img,
        }
        response = self.client.post(reverse('report-lost'), data=post_data)
        self.assertRedirects(response, reverse('dashboard'))

        item = Item.objects.get(title='Item with Photo')
        self.assertTrue(bool(item.image))
        self.assertTrue(item.image.name.startswith('items/'))


class DashboardAndDetailsViewsTest(TestCase):
    """
    Test suite verifying that user-submitted reports correctly appear on
    the user's dashboard and their details view renders dynamic data.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='reportowner',
            email='owner@findback.org',
            password='SecureOwnerPass123!'
        )
        self.other_user = User.objects.create_user(
            username='otherperson',
            email='other@findback.org',
            password='SecureOtherPass123!'
        )
        self.today = timezone.now().date()
        self.item = Item.objects.create(
            user=self.user,
            item_type=Item.ItemType.LOST,
            category=Item.ItemCategory.ELECTRONICS,
            title='MacBook Pro 16 Space Gray',
            description='Space gray laptop with stickers on back lid.',
            brand='Apple',
            color='Space Gray',
            location='Library 2nd Floor Study Room',
            date_occurred=self.today,
            identification_details='Serial C02X12345678 and blue skull sticker',
            status=Item.ItemStatus.ACTIVE
        )

    def test_dashboard_displays_user_reported_items(self):
        """Verify user's dashboard lists their reported items with live links."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'MacBook Pro 16 Space Gray')
        self.assertContains(response, 'Electronics')
        self.assertContains(response, 'Library 2nd Floor Study Room')
        self.assertContains(response, f'/items/{self.item.id}/')

    def test_dashboard_empty_state_for_new_user(self):
        """Verify empty state is displayed when user has no reports."""
        self.client.force_login(self.other_user)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No items reported yet')

    def test_item_details_view_by_owner_shows_private_markers(self):
        """Verify owner can view their submitted report and its private identification markers."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('item-detail', kwargs={'pk': self.item.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'MacBook Pro 16 Space Gray')
        self.assertContains(response, 'Library 2nd Floor Study Room')
        self.assertContains(response, 'Serial C02X12345678 and blue skull sticker')
        self.assertContains(response, 'Private ownership details')
        self.assertContains(response, 'These details are kept private and should not be shared publicly.')

    def test_item_details_idor_protection_returns_404_for_other_user(self):
        """Verify IDOR prevention: User B cannot access User A's item report (returns 404)."""
        self.client.force_login(self.other_user)
        response = self.client.get(reverse('item-detail', kwargs={'pk': self.item.pk}))
        self.assertEqual(response.status_code, 404)

    def test_item_details_nonexistent_id_returns_404(self):
        """Verify nonexistent item returns 404 safe error."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('item-detail', kwargs={'pk': 999999}))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_user_redirected_to_login(self):
        """Verify unauthenticated user attempting to view item is redirected to login."""
        response = self.client.get(reverse('item-detail', kwargs={'pk': self.item.pk}))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('item-detail', kwargs={'pk': self.item.pk})}")


class MyReportsViewTest(TestCase):
    """Test suite for the My Reports page and filtering."""

    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='password123')
        self.other_user = User.objects.create_user(username='bob', password='password123')
        self.today = timezone.now().date()

        self.lost_item = Item.objects.create(
            user=self.user,
            item_type=Item.ItemType.LOST,
            title='Lost Blue Backpack',
            category=Item.ItemCategory.BAG,
            location='Campus Library',
            date_occurred=self.today,
            description='Blue backpack lost on Monday'
        )
        self.found_item = Item.objects.create(
            user=self.user,
            item_type=Item.ItemType.FOUND,
            title='Found Silver Keys',
            category=Item.ItemCategory.KEYS,
            location='Cafeteria',
            date_occurred=self.today,
            description='Found silver keychain with 3 keys'
        )
        self.other_user_item = Item.objects.create(
            user=self.other_user,
            item_type=Item.ItemType.LOST,
            title='Bob Secret Item',
            category=Item.ItemCategory.OTHER,
            location='Gym',
            date_occurred=self.today,
            description='Belongs to Bob'
        )

    def test_my_reports_requires_login(self):
        """Verify unauthenticated access to my-reports redirects to login."""
        response = self.client.get(reverse('my-reports'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('my-reports')}")

    def test_my_reports_shows_only_current_user_items(self):
        """Verify only the logged-in user's items are displayed in My Reports."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('my-reports'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lost Blue Backpack')
        self.assertContains(response, 'Found Silver Keys')
        self.assertNotContains(response, 'Bob Secret Item')

    def test_my_reports_filter_lost(self):
        """Verify filtering by type=lost only shows LOST items."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('my-reports') + '?type=lost')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lost Blue Backpack')
        self.assertNotContains(response, 'Found Silver Keys')

    def test_my_reports_filter_found(self):
        """Verify filtering by type=found only shows FOUND items."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('my-reports') + '?type=found')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Found Silver Keys')
        self.assertNotContains(response, 'Lost Blue Backpack')

    def test_my_reports_filter_invalid_type_falls_back_to_all(self):
        """Verify invalid query parameter ?type=random safely falls back to all items."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('my-reports') + '?type=random')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lost Blue Backpack')
        self.assertContains(response, 'Found Silver Keys')

    def test_my_reports_empty_state(self):
        """Verify friendly empty state when user has no reports."""
        new_user = User.objects.create_user(username='charlie', password='password123')
        self.client.force_login(new_user)
        response = self.client.get(reverse('my-reports'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You haven't submitted any reports yet.")
        self.assertContains(response, reverse('report-lost'))
        self.assertContains(response, reverse('report-found'))


class ItemEditViewTest(TestCase):
    """Test suite for the Item Edit functionality."""

    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='password123')
        self.other_user = User.objects.create_user(username='bob', password='password123')
        self.today = timezone.now().date()
        self.item = Item.objects.create(
            user=self.user,
            item_type=Item.ItemType.LOST,
            status=Item.ItemStatus.ACTIVE,
            title='Black Leather Wallet',
            category=Item.ItemCategory.WALLET,
            brand='Fossil',
            color='Black',
            location='Library Hall',
            date_occurred=self.today,
            description='Lost near reception desk',
            identification_details='Contains library card #8821'
        )

    def test_edit_get_renders_form_with_current_data(self):
        """Verify owner GET /items/<id>/edit/ renders form pre-filled with item data."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('item-edit', kwargs={'pk': self.item.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Black Leather Wallet')
        self.assertContains(response, 'Fossil')
        self.assertContains(response, 'Library Hall')

    def test_edit_post_success_updates_item(self):
        """Verify valid POST successfully updates editable fields and redirects to item-detail."""
        self.client.force_login(self.user)
        post_data = {
            'title': 'Updated Brown Leather Wallet',
            'category': Item.ItemCategory.WALLET,
            'brand': 'Fossil Vintage',
            'color': 'Brown',
            'location': 'Library 1st Floor',
            'date_occurred': self.today.isoformat(),
            'description': 'Updated description with more details',
            'identification_details': 'Library card #8821 and driver license'
        }
        response = self.client.post(reverse('item-edit', kwargs={'pk': self.item.pk}), data=post_data)
        self.assertRedirects(response, reverse('item-detail', kwargs={'pk': self.item.pk}))

        self.item.refresh_from_db()
        self.assertEqual(self.item.title, 'Updated Brown Leather Wallet')
        self.assertEqual(self.item.brand, 'Fossil Vintage')
        self.assertEqual(self.item.color, 'Brown')
        self.assertEqual(self.item.location, 'Library 1st Floor')

        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Your item report has been updated successfully." in m.message for m in messages_list))

    def test_edit_cannot_change_item_type_or_status_or_user(self):
        """Verify server ignores any attempt to change item_type, status, or user during edit."""
        self.client.force_login(self.user)
        malicious_data = {
            'title': 'Attempted Spoof',
            'category': Item.ItemCategory.WALLET,
            'location': 'Library',
            'date_occurred': self.today.isoformat(),
            'description': 'Attempting to change type to FOUND and status to CLOSED',
            'item_type': 'FOUND',
            'status': 'CLOSED',
            'user': self.other_user.id
        }
        response = self.client.post(reverse('item-edit', kwargs={'pk': self.item.pk}), data=malicious_data)
        self.assertRedirects(response, reverse('item-detail', kwargs={'pk': self.item.pk}))

        self.item.refresh_from_db()
        self.assertEqual(self.item.item_type, Item.ItemType.LOST)
        self.assertEqual(self.item.status, Item.ItemStatus.ACTIVE)
        self.assertEqual(self.item.user, self.user)

    def test_edit_idor_protection_returns_404_for_other_user(self):
        """Verify User B cannot access or edit User A's item (returns 404)."""
        self.client.force_login(self.other_user)
        response_get = self.client.get(reverse('item-edit', kwargs={'pk': self.item.pk}))
        self.assertEqual(response_get.status_code, 404)

        response_post = self.client.post(reverse('item-edit', kwargs={'pk': self.item.pk}), data={'title': 'Hacked'})
        self.assertEqual(response_post.status_code, 404)
        self.item.refresh_from_db()
        self.assertNotEqual(self.item.title, 'Hacked')

    def test_edit_remove_image_safely_removes_file(self):
        """Verify checking remove_image safely deletes the file and clears image field."""
        import os
        test_img = create_test_image()
        self.item.image = test_img
        self.item.save()
        img_path = self.item.image.path
        self.assertTrue(os.path.exists(img_path))

        self.client.force_login(self.user)
        post_data = {
            'title': self.item.title,
            'category': self.item.category,
            'location': self.item.location,
            'date_occurred': self.item.date_occurred.isoformat(),
            'description': self.item.description,
            'remove_image': '1',
        }
        response = self.client.post(reverse('item-edit', kwargs={'pk': self.item.pk}), data=post_data)
        self.assertRedirects(response, reverse('item-detail', kwargs={'pk': self.item.pk}))

        self.item.refresh_from_db()
        self.assertFalse(bool(self.item.image))
        self.assertFalse(os.path.exists(img_path))



class ItemDeleteViewTest(TestCase):
    """Test suite for the Item Delete functionality."""

    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='password123')
        self.other_user = User.objects.create_user(username='bob', password='password123')
        self.today = timezone.now().date()
        self.item = Item.objects.create(
            user=self.user,
            item_type=Item.ItemType.LOST,
            title='Delete Me Item',
            category=Item.ItemCategory.BAG,
            location='Cafeteria',
            date_occurred=self.today,
            description='To be deleted'
        )

    def test_delete_get_renders_confirmation_without_deleting(self):
        """Verify GET /items/<id>/delete/ shows confirmation UI and does NOT delete item."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('item-delete', kwargs={'pk': self.item.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Are you sure you want to delete this report?')
        self.assertTrue(Item.objects.filter(pk=self.item.pk).exists())

    def test_delete_post_deletes_item_and_redirects(self):
        """Verify POST /items/<id>/delete/ successfully removes item and redirects to my-reports."""
        self.client.force_login(self.user)
        response = self.client.post(reverse('item-delete', kwargs={'pk': self.item.pk}))
        self.assertRedirects(response, reverse('my-reports'))
        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists())

        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Your item report has been deleted." in m.message for m in messages_list))

    def test_delete_idor_protection_returns_404_for_other_user(self):
        """Verify User B cannot delete User A's item (returns 404)."""
        self.client.force_login(self.other_user)
        response = self.client.post(reverse('item-delete', kwargs={'pk': self.item.pk}))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Item.objects.filter(pk=self.item.pk).exists())

    def test_delete_cleans_up_associated_image_file(self):
        """Verify deleting an item with an image deletes the file from disk safely."""
        import os
        test_img = create_test_image()
        item_with_img = Item.objects.create(
            user=self.user,
            item_type=Item.ItemType.LOST,
            title='Item With Image File',
            category=Item.ItemCategory.ELECTRONICS,
            location='Library',
            date_occurred=self.today,
            description='Has an image file',
            image=test_img
        )
        img_path = item_with_img.image.path
        self.assertTrue(os.path.exists(img_path))

        self.client.force_login(self.user)
        response = self.client.post(reverse('item-delete', kwargs={'pk': item_with_img.pk}))
        self.assertRedirects(response, reverse('my-reports'))
        self.assertFalse(os.path.exists(img_path))


