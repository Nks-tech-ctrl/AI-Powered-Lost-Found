from django.test import TestCase, Client, override_settings
from django.urls import reverse
from core.views import custom_404_view, custom_500_view, custom_403_view, custom_400_view
from django.test import RequestFactory


class ErrorPagesTest(TestCase):
    """Test suite verifying error pages render properly with correct HTTP statuses."""

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

    def test_home_page_status_200(self):
        """Verify the homepage renders with 200 OK."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/index.html')

    def test_preview_404_view_renders_correctly(self):
        """Verify preview-404 route returns 404 status and renders 404.html template."""
        response = self.client.get(reverse('preview-404'))
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')
        self.assertContains(response, "Report or Page", status_code=404)
        self.assertContains(response, "Not Found", status_code=404)

    def test_preview_500_view_renders_correctly(self):
        """Verify preview-500 route returns 500 status and renders 500.html template."""
        response = self.client.get(reverse('preview-500'))
        self.assertEqual(response.status_code, 500)
        self.assertTemplateUsed(response, '500.html')
        self.assertContains(response, "System", status_code=500)
        self.assertContains(response, "500 Error", status_code=500)

    def test_preview_403_view_renders_correctly(self):
        """Verify preview-403 route returns 403 status and renders 403.html template."""
        response = self.client.get(reverse('preview-403'))
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')
        self.assertContains(response, "Access", status_code=403)
        self.assertContains(response, "Restricted", status_code=403)

    def test_preview_400_view_renders_correctly(self):
        """Verify preview-400 route returns 400 status and renders 400.html template."""
        response = self.client.get(reverse('preview-400'))
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(response, '400.html')
        self.assertContains(response, "Invalid", status_code=400)
        self.assertContains(response, "Request", status_code=400)

    def test_custom_404_view_function(self):
        """Directly invoke custom_404_view and verify response."""
        request = self.factory.get('/nonexistent-test-url/')
        response = custom_404_view(request, exception=Exception("Page does not exist"))
        self.assertEqual(response.status_code, 404)

    def test_custom_500_view_function(self):
        """Directly invoke custom_500_view and verify response."""
        request = self.factory.get('/some-broken-url/')
        response = custom_500_view(request)
        self.assertEqual(response.status_code, 500)

    def test_custom_403_view_function(self):
        """Directly invoke custom_403_view and verify response."""
        request = self.factory.get('/forbidden-url/')
        response = custom_403_view(request)
        self.assertEqual(response.status_code, 403)

    def test_custom_400_view_function(self):
        """Directly invoke custom_400_view and verify response."""
        request = self.factory.get('/bad-request-url/')
        response = custom_400_view(request)
        self.assertEqual(response.status_code, 400)
