from django.apps import AppConfig


class TurnstileHtmxConfig(AppConfig):
    """
    Configuration for the Cloudflare Turnstile HTMX integration app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'turnstile_htmx'
    verbose_name = 'Turnstile HTMX'
