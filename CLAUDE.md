# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Installation
- `python -m venv .venv && source .venv/bin/activate` - Create and activate virtual environment
- `pip install -e '.[test]'` - Install package in editable mode with test dependencies

### Testing
- `pytest` - Run all tests (configured via pyproject.toml)
- `pytest turnstile_htmx/tests/templatetags_test.py` - Run template tag tests only
- `pytest turnstile_htmx/tests/integration_test.py` - Run integration tests only
- `pytest -v` - Run tests with verbose output

### Package Building
- `python -m build` - Build distribution packages for PyPI
- `pip install build` - Install build tool if not available

## Architecture Overview

This is a Django reusable app that provides Cloudflare Turnstile CAPTCHA integration with HTMX support. The package follows modern Python packaging standards with pyproject.toml configuration.

### Core Components

**Django App Structure:**
- `turnstile_htmx/apps.py` - Django app configuration
- `turnstile_htmx/decorators.py` - View decorator for server-side validation
- `turnstile_htmx/templatetags/turnstile_tags.py` - Template tags for frontend integration

**Key Architecture Patterns:**

1. **Dual Request Handling**: The `@turnstile_protected` decorator automatically detects HTMX requests via `HX-Request` header and returns appropriate response formats (HTML fragments for HTMX, full error pages for regular requests).

2. **Template Tag Integration**: `{% turnstile_field %}` generates JavaScript that handles both regular form submissions and HTMX form submissions by intercepting events and rendering Turnstile widgets on-demand.

3. **Server-side Validation**: The decorator validates tokens via Cloudflare's API using the `requests` library, extracting client IP from X-Forwarded-For headers for proper validation.

### Configuration Requirements

The app requires two Django settings:
- `CLOUDFLARE_TURNSTILE_SITE_KEY` - Public site key for frontend
- `CLOUDFLARE_TURNSTILE_SECRET_KEY` - Private key for server validation

### Test Configuration

Tests use a minimal Django project in `turnstile_htmx/tests/test_project/settings.py` with:
- In-memory SQLite database
- Django templates backend configured
- Test Turnstile keys for validation testing

The pytest configuration in pyproject.toml automatically uses this test project settings module.

### Dependencies

- `django>=4.2` - Django framework
- `requests` - HTTP library for Cloudflare API calls
- `pytest` and `pytest-django` - Testing framework (dev dependency)

### Frontend Integration Notes

The template tags generate JavaScript that:
- Prevents form submission until Turnstile validation completes
- Handles both HTMX and regular form submission patterns
- Uses unique container IDs to support multiple widgets per page
- Includes proper error handling and widget cleanup