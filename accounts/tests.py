import tempfile
import shutil
from io import BytesIO
from PIL import Image

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import UserProfile


def create_test_image(fmt='JPEG', filename='test.jpg'):
    """Helper to generate a valid in-memory test image."""
    file = BytesIO()
    image = Image.new('RGB', (100, 100), color=(37, 99, 235))
    image.save(file, format=fmt)
    file.seek(0)
    content_type = 'image/jpeg' if fmt == 'JPEG' else f'image/{fmt.lower()}'
    return SimpleUploadedFile(filename, file.read(), content_type=content_type)


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_password = "SecurePassword123!"
        self.user = User.objects.create_user(
            username="abhishek",
            email="abhishek@example.com",
            password=self.user_password,
            first_name="Abhishek",
            last_name="Sharma"
        )

    def test_registration_success(self):
        """Test registration creates user with hashed password, creates UserProfile, and redirects to login."""
        response = self.client.post(reverse('register'), {
            'first_name': 'Rahul',
            'last_name': 'Verma',
            'username': 'rahul_v',
            'email': 'rahul@example.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
        })
        self.assertRedirects(response, reverse('login'))

        # Verify user exists in database and password is encrypted
        new_user = User.objects.get(username='rahul_v')
        self.assertEqual(new_user.first_name, 'Rahul')
        self.assertEqual(new_user.last_name, 'Verma')
        self.assertEqual(new_user.email, 'rahul@example.com')
        self.assertTrue(new_user.check_password('StrongPassword123!'))
        self.assertNotEqual(new_user.password, 'StrongPassword123!')  # Must be hashed

        # Verify UserProfile was automatically created via post_save signal
        self.assertTrue(hasattr(new_user, 'profile'))
        self.assertIsInstance(new_user.profile, UserProfile)
        self.assertTrue(new_user.profile.match_notifications)
        self.assertTrue(new_user.profile.claim_notifications)
        self.assertTrue(new_user.profile.report_notifications)
        self.assertTrue(new_user.profile.community_notifications)

        # Verify success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Account created successfully" in str(m) for m in messages))

    def test_registration_duplicate_username(self):
        """Test registration prevents duplicate username with friendly error."""
        response = self.client.post(reverse('register'), {
            'first_name': 'Another',
            'last_name': 'User',
            'username': 'abhishek',  # Already exists
            'email': 'another@example.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'username', "This username is already taken.")

    def test_registration_duplicate_email(self):
        """Test registration prevents duplicate email with friendly error."""
        response = self.client.post(reverse('register'), {
            'first_name': 'Another',
            'last_name': 'User',
            'username': 'unique_user',
            'email': 'abhishek@example.com',  # Already exists
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'email', "An account with this email address already exists.")

    def test_registration_password_mismatch(self):
        """Test registration validates confirm password matches password."""
        response = self.client.post(reverse('register'), {
            'first_name': 'Priya',
            'last_name': 'Patel',
            'username': 'priya_p',
            'email': 'priya@example.com',
            'password': 'Password12345!',
            'confirm_password': 'DifferentPassword999!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'confirm_password', "Passwords do not match.")

    def test_login_success_with_username(self):
        """Test login with valid username credentials."""
        response = self.client.post(reverse('login'), {
            'username': 'abhishek',
            'password': self.user_password,
            'remember_me': True,
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_login_success_with_email(self):
        """Test login allows registered email address in username field."""
        response = self.client.post(reverse('login'), {
            'username': 'abhishek@example.com',
            'password': self.user_password,
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_login_remember_me_expiry(self):
        """Test remember me flag sets session expiry."""
        self.client.post(reverse('login'), {
            'username': 'abhishek',
            'password': self.user_password,
            'remember_me': False,
        })
        self.assertTrue(self.client.session.get_expire_at_browser_close())

        self.client.logout()

        self.client.post(reverse('login'), {
            'username': 'abhishek',
            'password': self.user_password,
            'remember_me': True,
        })
        self.assertFalse(self.client.session.get_expire_at_browser_close())

    def test_login_invalid_credentials_generic_message(self):
        """Test invalid credentials display generic error message without leaking details."""
        response = self.client.post(reverse('login'), {
            'username': 'abhishek',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Invalid username or password." in str(m) for m in messages))

    def test_login_redirect_with_next_param(self):
        """Test login returns user to requested page using ?next= parameter."""
        response = self.client.post(f"{reverse('login')}?next=/items/report-lost/", {
            'username': 'abhishek',
            'password': self.user_password,
        })
        self.assertRedirects(response, '/items/report-lost/')

    def test_logout_redirects_and_clears_session(self):
        """Test logout clears session, displays message, and redirects to home."""
        self.client.login(username='abhishek', password=self.user_password)
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, '/')
        self.assertNotIn('_auth_user_id', self.client.session)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("You have been logged out successfully." in str(m) for m in messages))

    def test_protected_pages_redirect_unauthenticated(self):
        """Test protected routes redirect unauthenticated users to login with ?next=."""
        protected_urls = [
            '/dashboard/',
            '/items/report-lost/',
            '/items/report-found/',
            '/matches/',
            '/claims/',
            '/accounts/profile/',
        ]
        for url in protected_urls:
            response = self.client.get(url)
            expected_redirect = f"{reverse('login')}?next={url}"
            self.assertRedirects(response, expected_redirect)

    def test_public_pages_accessible_without_auth(self):
        """Test public pages are accessible without login."""
        public_urls = [
            '/',
            '/accounts/login/',
            '/accounts/register/',
        ]
        for url in public_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_dashboard_displays_user_greeting(self):
        """Test dashboard welcomes authenticated user by first name."""
        self.client.login(username='abhishek', password=self.user_password)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome back')
        self.assertContains(response, 'Abhishek')


class UserProfileTests(TestCase):
    """
    Test suite for Step 5: Dynamic User Profile System.
    Validates model, signals, forms, view permissions, photo uploads,
    and profile privacy isolation.
    """
    def setUp(self):
        self.temp_media_dir = tempfile.mkdtemp()
        self.client = Client()
        self.password = "StrongPassword99!"
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password=self.password,
            first_name="Test",
            last_name="User"
        )
        self.second_user = User.objects.create_user(
            username="seconduser",
            email="second@example.com",
            password=self.password,
            first_name="Second",
            last_name="Person"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_media_dir, ignore_errors=True)

    def test_signal_creates_profile_automatically(self):
        """Verify UserProfile is automatically created when a new user is created."""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertEqual(self.user.profile.user, self.user)
        self.assertEqual(str(self.user.profile), "testuser")
        self.assertTrue(self.user.profile.match_notifications)
        self.assertTrue(self.user.profile.claim_notifications)
        self.assertTrue(self.user.profile.report_notifications)
        self.assertTrue(self.user.profile.community_notifications)

    def test_profile_view_displays_authenticated_user_details(self):
        """Verify GET /accounts/profile/ displays authenticated user credentials."""
        self.client.login(username="testuser", password=self.password)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
        self.assertContains(response, "Test User")
        self.assertContains(response, "@testuser")
        self.assertContains(response, "testuser@example.com")
        self.assertContains(response, "Member since")

    def test_profile_update_personal_info(self):
        """Verify POST /accounts/profile/ updates first name, last name, email, phone, location, bio."""
        self.client.login(username="testuser", password=self.password)
        response = self.client.post(reverse('profile'), {
            'first_name': 'UpdatedFirst',
            'last_name': 'UpdatedLast',
            'email': 'updated@example.com',
            'phone': '+1 (555) 987-6543',
            'location': 'San Francisco, CA',
            'bio': 'Passionate community helper and Python developer.',
            'match_notifications': True,
            'claim_notifications': True,
            'report_notifications': True,
            'community_notifications': True,
        })
        self.assertRedirects(response, reverse('profile'))

        # Verify database changes
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, 'UpdatedFirst')
        self.assertEqual(self.user.last_name, 'UpdatedLast')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.profile.phone, '+1 (555) 987-6543')
        self.assertEqual(self.user.profile.location, 'San Francisco, CA')
        self.assertEqual(self.user.profile.bio, 'Passionate community helper and Python developer.')

        # Verify success message was dispatched
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Profile updated successfully." in str(m) for m in messages))

    def test_profile_update_notification_preferences(self):
        """Verify notification toggles can be disabled and saved."""
        self.client.login(username="testuser", password=self.password)
        response = self.client.post(reverse('profile'), {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'email': self.user.email,
            'phone': '1234567890',
            'location': 'New York',
            'bio': 'Testing notifications',
            # Unchecking all notification toggles
        })
        self.assertRedirects(response, reverse('profile'))

        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.match_notifications)
        self.assertFalse(self.user.profile.claim_notifications)
        self.assertFalse(self.user.profile.report_notifications)
        self.assertFalse(self.user.profile.community_notifications)

    def test_profile_picture_upload_valid_image(self):
        """Verify uploading a valid JPG profile picture works and file is stored in media/profiles/."""
        with override_settings(MEDIA_ROOT=self.temp_media_dir):
            self.client.login(username="testuser", password=self.password)
            image_file = create_test_image(fmt='JPEG', filename='avatar.jpg')
            response = self.client.post(reverse('profile'), {
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'email': self.user.email,
                'phone': '',
                'location': '',
                'bio': '',
                'match_notifications': True,
                'claim_notifications': True,
                'report_notifications': True,
                'community_notifications': True,
                'profile_picture': image_file,
            })
            self.assertRedirects(response, reverse('profile'))

            self.user.profile.refresh_from_db()
            self.assertTrue(bool(self.user.profile.profile_picture))
            self.assertTrue(self.user.profile.profile_picture.name.startswith('profiles/'))

            # Verify image appears on subsequent profile page load
            profile_page = self.client.get(reverse('profile'))
            self.assertContains(profile_page, self.user.profile.profile_picture.url)

    def test_profile_picture_upload_invalid_file(self):
        """Verify uploading an invalid text/executable file is rejected with a clean message."""
        self.client.login(username="testuser", password=self.password)
        fake_image = SimpleUploadedFile(
            "malicious.txt",
            b"This is not a real image.",
            content_type="text/plain"
        )
        response = self.client.post(reverse('profile'), {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'email': self.user.email,
            'phone': '',
            'location': '',
            'bio': '',
            'match_notifications': True,
            'claim_notifications': True,
            'report_notifications': True,
            'community_notifications': True,
            'profile_picture': fake_image,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context['profile_form'],
            'profile_picture',
            "Please upload a valid image file."
        )

    def test_profile_isolation_between_different_users(self):
        """Verify users can only see their own profile and cannot view another user's info."""
        # Set distinct profiles
        self.user.profile.location = "Mumbai"
        self.user.profile.save()

        self.second_user.profile.location = "Bengaluru"
        self.second_user.profile.save()

        # Login as testuser -> only see Mumbai
        self.client.login(username="testuser", password=self.password)
        response_one = self.client.get(reverse('profile'))
        self.assertContains(response_one, "@testuser")
        self.assertContains(response_one, "Mumbai")
        self.assertNotContains(response_one, "@seconduser")
        self.assertNotContains(response_one, "Bengaluru")

        # Logout and login as seconduser -> only see Bengaluru
        self.client.logout()
        self.client.login(username="seconduser", password=self.password)
        response_two = self.client.get(reverse('profile'))
        self.assertContains(response_two, "@seconduser")
        self.assertContains(response_two, "Bengaluru")
        self.assertNotContains(response_two, "@testuser")
        self.assertNotContains(response_two, "Mumbai")

    def test_unauthenticated_profile_access_redirects(self):
        """Verify anonymous user cannot access /accounts/profile/."""
        response = self.client.get(reverse('profile'))
        self.assertRedirects(response, f"{reverse('login')}?next=/accounts/profile/")
