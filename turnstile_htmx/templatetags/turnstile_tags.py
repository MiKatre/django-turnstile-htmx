import uuid

from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.translation import gettext as _

register = template.Library()


@register.simple_tag
def turnstile_field(
    container_id=None,
    site_key=None,
    action=None,
    appearance="always",
    unavailable_message=None,
    error_message=None,
    expired_message=None,
):
    """Render a progressively enhanced Turnstile field for the nearest form."""
    site_key = site_key or getattr(settings, "CLOUDFLARE_TURNSTILE_SITE_KEY", "")
    container_id = container_id or f"turnstile-container-{uuid.uuid4().hex[:8]}"

    return format_html(
        '<div id="{}" class="turnstile-widget" data-turnstile-container '
        'data-sitekey="{}" data-action="{}" data-appearance="{}" '
        'data-turnstile-unavailable-message="{}" '
        'data-turnstile-error-message="{}" '
        'data-turnstile-expired-message="{}" hidden></div>'
        '<p class="turnstile-error" role="alert" data-turnstile-error hidden></p>',
        container_id,
        site_key,
        action or "",
        appearance,
        unavailable_message
        or _("The security check could not be loaded. Please try again."),
        error_message or _("The security check failed. Please try again."),
        expired_message or _("The security check expired. Please try again."),
    )


@register.simple_tag
def turnstile_script():
    """Render Cloudflare's API and the package's form integration once."""
    return format_html(
        '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit" '
        'async defer></script><script src="{}" defer></script>',
        static("turnstile_htmx/turnstile.js"),
    )
