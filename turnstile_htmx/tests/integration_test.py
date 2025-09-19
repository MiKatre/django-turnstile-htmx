# tests/test_integration.py
from unittest.mock import patch

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

from turnstile_htmx.decorators import turnstile_protected


class TurnstileIntegrationTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # Create test view
        @turnstile_protected
        def test_view(request):
            return HttpResponse("Success")

        self.test_view = test_view

    @patch('turnstile_htmx.decorators.check_turnstile_token')
    def test_form_with_turnstile_submission(self, mock_check):
        """Test submitting a form with Turnstile token"""
        mock_check.return_value = True

        request = self.factory.post('/test-view/', {
            'name': 'Test User',
            'cf-turnstile-response': 'valid-token'
        })

        response = self.test_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Success")
        mock_check.assert_called_once()

    @patch('turnstile_htmx.decorators.check_turnstile_token')
    def test_htmx_request_with_turnstile(self, mock_check):
        """Test submitting via HTMX with Turnstile token"""
        mock_check.return_value = True

        request = self.factory.post('/test-view/', {'cf-turnstile-response': 'valid-token'})
        request.headers = {'HX-Request': 'true'}  # Set HTMX request header

        response = self.test_view(request)
        self.assertEqual(response.status_code, 200)
        mock_check.assert_called_once()
