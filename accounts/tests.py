from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages


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
        """Test registration creates user with hashed password and redirects to login."""
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
        self.assertFormError(response, 'form', 'username', "This username is already taken.")

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
        self.assertFormError(response, 'form', 'email', "An account with this email address already exists.")

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
        self.assertFormError(response, 'form', 'confirm_password', "Passwords do not match.")

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
        # Unchecked remember me -> session expires on browser close (set_expiry(0))
        self.client.post(reverse('login'), {
            'username': 'abhishek',
            'password': self.user_password,
            'remember_me': False,
        })
        self.assertTrue(self.client.session.get_expire_at_browser_close())

        self.client.logout()

        # Checked remember me -> Django normal session behavior
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

    def test_profile_page_displays_user_data(self):
        """Test authenticated user sees their account details on profile page."""
        self.client.login(username='abhishek', password=self.user_password)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Abhishek Sharma')
        self.assertContains(response, 'abhishek')
        self.assertContains(response, 'abhishek@example.com')

    def test_dashboard_displays_user_greeting(self):
        """Test dashboard welcomes authenticated user by first name."""
        self.client.login(username='abhishek', password=self.user_password)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome back')
        self.assertContains(response, 'Abhishek')
