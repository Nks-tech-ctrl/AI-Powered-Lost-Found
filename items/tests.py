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
        response = self.client.get(reverse('item_details_id', kwargs={'id': self.item.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'MacBook Pro 16 Space Gray')
        self.assertContains(response, 'Library 2nd Floor Study Room')
        self.assertContains(response, 'Serial C02X12345678 and blue skull sticker')
        self.assertContains(response, 'Your Private Identification Markers')
        self.assertContains(response, 'You submitted this report')

    def test_item_details_view_by_other_user_shields_private_markers(self):
        """Verify other users cannot see private identification markers."""
        self.client.force_login(self.other_user)
        response = self.client.get(reverse('item_details_id', kwargs={'id': self.item.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'MacBook Pro 16 Space Gray')
        self.assertNotContains(response, 'Serial C02X12345678 and blue skull sticker')
        self.assertContains(response, 'Hidden Verification Challenge Active')

    def test_item_details_nonexistent_id_renders_empty_state(self):
        """Verify invalid or nonexistent ID renders friendly not found page."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('item_details_id', kwargs={'id': '999999'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Item Report Not Found')
