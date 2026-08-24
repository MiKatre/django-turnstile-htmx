import functools
import logging

import requests
from django.conf import settings
from django.http import HttpResponseBadRequest
from django.utils.html import format_html
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
DEFAULT_TIMEOUT_SECONDS = 5
TURNSTILE_ALWAYS_PASS_TEST_SECRET = "1x0000000000000000000000000000000AA"


def get_client_ip(request):
    """Return the direct peer address without trusting client-supplied proxy headers."""
    return request.META.get("REMOTE_ADDR")


def _normalise_hostnames(hostnames):
    if not hostnames:
        return ()
    if isinstance(hostnames, str):
        return (hostnames,)
    return tuple(hostnames)


def check_turnstile_token(request, *, action=None, hostnames=None):
    """Validate a Turnstile token with Cloudflare's Siteverify endpoint."""
    token = request.POST.get("cf-turnstile-response")
    if not token:
        return False

    secret_key = getattr(settings, "CLOUDFLARE_TURNSTILE_SECRET_KEY", "")
    if not secret_key:
        logger.error("Turnstile validation is unavailable: secret key is not configured")
        return False

    expected_hostnames = _normalise_hostnames(
        hostnames
        if hostnames is not None
        else getattr(settings, "CLOUDFLARE_TURNSTILE_EXPECTED_HOSTNAMES", ())
    )
    timeout = getattr(
        settings,
        "CLOUDFLARE_TURNSTILE_TIMEOUT_SECONDS",
        DEFAULT_TIMEOUT_SECONDS,
    )

    data = {"secret": secret_key, "response": token}
    remote_ip = get_client_ip(request)
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        response = requests.post(SITEVERIFY_URL, data=data, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        logger.warning("Turnstile Siteverify request failed", exc_info=True)
        return False

    if not payload.get("success", False):
        logger.info(
            "Turnstile rejected a token: %s",
            payload.get("error-codes", ()),
        )
        return False

    is_official_test_response = (
        secret_key == TURNSTILE_ALWAYS_PASS_TEST_SECRET
        and payload.get("metadata", {}).get("result_with_testing_key") is True
    )
    if action and payload.get("action") != action and not is_official_test_response:
        logger.warning("Turnstile token action did not match the protected action")
        return False

    if (
        expected_hostnames
        and payload.get("hostname") not in expected_hostnames
        and not is_official_test_response
    ):
        logger.warning("Turnstile token hostname was not allowed")
        return False

    return True


def turnstile_protected(
    view_func=None,
    *,
    action=None,
    hostnames=None,
):
    """Require a valid Turnstile token before executing a POST view."""

    def decorator(_view_func):
        @functools.wraps(_view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.method == "POST" and not check_turnstile_token(
                request,
                action=action,
                hostnames=hostnames,
            ):
                if request.headers.get("HX-Request"):
                    return HttpResponseBadRequest(
                        format_html(
                            '<div class="turnstile-error-container" role="alert">'
                            '<strong>{}</strong><p>{}</p></div>',
                            _("Verification failed"),
                            _("Please complete the security check and try again."),
                        )
                    )
                return HttpResponseBadRequest(
                    _("Security verification failed. Please try again.")
                )

            return _view_func(request, *args, **kwargs)

        return _wrapped_view

    if view_func:
        return decorator(view_func)
    return decorator
