import functools

import requests
from django.conf import settings
from django.http import HttpResponseBadRequest
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def check_turnstile_token(request):
    """Validate Turnstile token with Cloudflare API."""
    token = request.POST.get("cf-turnstile-response")
    if not token:
        return False

    remoteip = get_client_ip(request)
    secret_key = getattr(settings, 'CLOUDFLARE_TURNSTILE_SECRET_KEY', '')

    data = {"secret": secret_key, "response": token, "remoteip": remoteip}
    url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

    try:
        response = requests.post(url, data)
        if response.ok:
            response = response.json()
            return response.get("success", False)
    except Exception:
        pass

    return False


def turnstile_protected(view_func=None, *, error_template=None):
    """
    Decorator that validates Cloudflare Turnstile CAPTCHA token.

    Works with both regular Django views and HTMX requests.

    Args:
        view_func: The view function to decorate
        error_template: Optional custom HTML to display on validation error

    Usage:
        @turnstile_protected
        def my_view(request):
            # Your view code here

        # OR with custom error template
        @turnstile_protected(error_template='<div>Custom error</div>')
        def my_view(request):
            # Your view code here
    """
    def decorator(_view_func):
        @functools.wraps(_view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Only validate on POST requests
            if request.method == "POST":
                turnstile_valid = check_turnstile_token(request)
                if not turnstile_valid:
                    # For HTMX requests, return properly formatted response
                    if request.headers.get('HX-Request'):
                        error_html = error_template or mark_safe(
                            '<div class="error-container">'
                            '<h3 class="text-xl font-semibold mb-2">' + _("Verification Failed") + '</h3>'
                            '<p class="mb-4">' + _("CAPTCHA verification failed. Please reload and try again.") + '</p>'
                            '</div>'
                        )
                        return HttpResponseBadRequest(error_html)
                    # For regular requests, return bad request with message
                    return HttpResponseBadRequest(_("CAPTCHA verification failed. Please try again."))

            # Call the view function if validation passes or not required
            return _view_func(request, *args, **kwargs)
        return _wrapped_view

    if view_func:
        return decorator(view_func)
    return decorator
