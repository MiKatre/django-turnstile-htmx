# tests/test_integration.py
from unittest.mock import Mock, patch

import requests
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from turnstile_htmx.decorators import (SITEVERIFY_URL, check_turnstile_token,
                                       turnstile_protected)


class TurnstileIntegrationTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # Create test view
        @turnstile_protected
        def test_view(request):
            return HttpResponse("Success")

        self.test_view = test_view

    @override_settings(
        CLOUDFLARE_TURNSTILE_SECRET_KEY="test-secret",
        CLOUDFLARE_TURNSTILE_EXPECTED_HOSTNAMES=("example.com",),
    )
    @patch("turnstile_htmx.decorators.requests.post")
    def test_siteverify_validates_action_hostname_and_timeout(self, mock_post):
        response = Mock()
        response.json.return_value = {
            "success": True,
            "hostname": "example.com",
            "action": "free_preview",
        }
        mock_post.return_value = response
        request = self.factory.post(
            "/test-view/",
            {"cf-turnstile-response": "valid-token"},
            REMOTE_ADDR="203.0.113.10",
        )

        self.assertTrue(check_turnstile_token(request, action="free_preview"))
        mock_post.assert_called_once_with(
            SITEVERIFY_URL,
            data={
                "secret": "test-secret",
                "response": "valid-token",
                "remoteip": "203.0.113.10",
            },
            timeout=5,
        )
        response.raise_for_status.assert_called_once_with()

    @override_settings(
        CLOUDFLARE_TURNSTILE_SECRET_KEY="test-secret",
        CLOUDFLARE_TURNSTILE_EXPECTED_HOSTNAMES=("example.com",),
    )
    @patch("turnstile_htmx.decorators.requests.post")
    def test_siteverify_rejects_wrong_action_or_hostname(self, mock_post):
        response = Mock()
        mock_post.return_value = response
        request = self.factory.post(
            "/test-view/",
            {"cf-turnstile-response": "valid-token"},
        )

        response.json.return_value = {
            "success": True,
            "hostname": "example.com",
            "action": "another_action",
        }
        self.assertFalse(check_turnstile_token(request, action="free_preview"))

        response.json.return_value = {
            "success": True,
            "hostname": "attacker.example",
            "action": "free_preview",
        }
        self.assertFalse(check_turnstile_token(request, action="free_preview"))

    @override_settings(
        CLOUDFLARE_TURNSTILE_SECRET_KEY=(
            "1x0000000000000000000000000000000AA"
        ),
        CLOUDFLARE_TURNSTILE_EXPECTED_HOSTNAMES=("localhost",),
    )
    @patch("turnstile_htmx.decorators.requests.post")
    def test_official_always_pass_key_accepts_cloudflare_test_response(self, mock_post):
        request = self.factory.post(
            "/submit/",
            {"cf-turnstile-response": "XXXX.DUMMY.TOKEN.XXXX"},
            REMOTE_ADDR="127.0.0.1",
        )
        response = Mock()
        response.json.return_value = {
            "success": True,
            "hostname": "example.com",
            "metadata": {"result_with_testing_key": True},
        }
        mock_post.return_value = response

        self.assertTrue(check_turnstile_token(request, action="free_preview"))

    @override_settings(CLOUDFLARE_TURNSTILE_SECRET_KEY="test-secret")
    @patch("turnstile_htmx.decorators.requests.post")
    def test_siteverify_fails_closed_on_cloudflare_error(self, mock_post):
        mock_post.side_effect = requests.RequestException("network unavailable")
        request = self.factory.post(
            "/test-view/",
            {"cf-turnstile-response": "valid-token"},
        )

        self.assertFalse(check_turnstile_token(request))

    @override_settings(CLOUDFLARE_TURNSTILE_SECRET_KEY="")
    @patch("turnstile_htmx.decorators.requests.post")
    def test_siteverify_fails_closed_without_secret(self, mock_post):
        request = self.factory.post(
            "/test-view/",
            {"cf-turnstile-response": "valid-token"},
        )

        self.assertFalse(check_turnstile_token(request))
        mock_post.assert_not_called()

    @patch("turnstile_htmx.decorators.check_turnstile_token")
    def test_form_with_turnstile_submission(self, mock_check):
        mock_check.return_value = True

        request = self.factory.post(
            "/test-view/",
            {
                "name": "Test User",
                "cf-turnstile-response": "valid-token",
            },
        )

        response = self.test_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Success")
        mock_check.assert_called_once()

    @patch("turnstile_htmx.decorators.check_turnstile_token")
    def test_decorator_passes_expected_action_and_hostname(self, mock_check):
        mock_check.return_value = True

        @turnstile_protected(action="free_preview", hostnames=("example.com",))
        def protected_view(request):
            return HttpResponse("Success")

        request = self.factory.post(
            "/test-view/",
            {"cf-turnstile-response": "valid-token"},
        )

        response = protected_view(request)

        self.assertEqual(response.status_code, 200)
        mock_check.assert_called_once_with(
            request,
            action="free_preview",
            hostnames=("example.com",),
        )

    @patch("turnstile_htmx.decorators.check_turnstile_token", return_value=False)
    def test_htmx_failure_returns_accessible_retry_fragment(self, _mock_check):
        request = self.factory.post(
            "/test-view/",
            {"cf-turnstile-response": "invalid-token"},
            HTTP_HX_REQUEST="true",
        )

        response = self.test_view(request)

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'role="alert"', status_code=400)
