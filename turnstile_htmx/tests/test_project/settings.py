# A minimal settings file for running the tests for turnstile_htmx
SECRET_KEY = "dummy-key-for-testing"

INSTALLED_APPS = [
    "turnstile_htmx",
]

# Template engine configuration for template tag tests
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

# The decorator needs these settings to be present
CLOUDFLARE_TURNSTILE_SITE_KEY = '1x0000000000000000000000000000000AA'
CLOUDFLARE_TURNSTILE_SECRET_KEY = '1x0000000000000000000000000000000AA'

# Use an in-memory SQLite database for fast tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}