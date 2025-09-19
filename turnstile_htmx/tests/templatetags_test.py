from django.template import Context, Template
from django.test import TestCase


class TurnstileTemplateTagsTests(TestCase):
    def test_turnstile_script_rendering(self):
        """Test that turnstile_script renders the correct script tag"""
        template = Template("{% load turnstile_tags %}{% turnstile_script %}")
        rendered = template.render(Context({}))

        self.assertIn('challenges.cloudflare.com/turnstile/v0/api.js', rendered)
        self.assertIn('async defer', rendered)

    def test_turnstile_field_rendering(self):
        """Test that turnstile_field renders with default settings"""
        template = Template("{% load turnstile_tags %}{% turnstile_field %}")

        with self.settings(CLOUDFLARE_TURNSTILE_SITE_KEY='test-site-key'):
            rendered = template.render(Context({}))

        self.assertIn('turnstile-widget', rendered)
        self.assertIn('test-site-key', rendered)
        self.assertIn('renderTurnstile', rendered)

    def test_turnstile_field_with_custom_container(self):
        """Test turnstile_field with custom container ID"""
        template = Template("{% load turnstile_tags %}{% turnstile_field container_id='custom-id' %}")
        rendered = template.render(Context({}))

        self.assertIn('id="custom-id"', rendered)

    def test_turnstile_field_with_custom_site_key(self):
        """Test turnstile_field with custom site key"""
        template = Template("{% load turnstile_tags %}{% turnstile_field site_key='custom-key' %}")
        rendered = template.render(Context({}))

        self.assertIn('custom-key', rendered)
