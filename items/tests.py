import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.admin.sites import site
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Item
from .forms import ItemForm
from .admin import ItemAdmin


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
        
        # Check validation error message
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
        # Should not raise
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
            category=Item.ItemCategory.PEN if hasattr(Item.ItemCategory, 'PEN') else Item.ItemCategory.OTHER,
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
        form = ItemForm(data=form_data, item_type=Item.ItemType.LOST)
        self.assertTrue(form.is_valid(), form.errors)
        item = form.save(commit=False)
        item.user = self.user
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
        """Test that user, status, created_at, updated_at are not editable fields in the form."""
        form = ItemForm()
        self.assertNotIn('user', form.fields)
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
