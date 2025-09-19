import uuid

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()
@register.simple_tag
def turnstile_field(container_id=None, site_key=None):
    """Renders the Cloudflare Turnstile field in a form."""
    # Use default site key if not provided
    site_key = site_key or getattr(settings, 'CLOUDFLARE_TURNSTILE_SITE_KEY', '1x0000000000000000000000000000000AA')

    # Generate unique container ID if not provided
    container_id = container_id or f'turnstile-container-{uuid.uuid4().hex[:8]}'

    html = f"""
    <div id="{container_id}" class="turnstile-widget w-full"></div>
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        // Check if this script has already run for this container
        if (window.turnstileInitialized && window.turnstileInitialized['{container_id}']) {{
            return;
        }}

        // Initialize tracking object if it doesn't exist
        if (!window.turnstileInitialized) {{
            window.turnstileInitialized = {{}};
        }}

        const container = document.getElementById('{container_id}');
        if (!container) return;

        const form = container.closest('form');
        if (!form) return;

        let isValidated = false;
        let isProcessing = false; // Prevent multiple simultaneous calls

        // Store original form data and submission details
        let originalEvent = null;
        let isHtmxSubmission = false;

        // Mark this container as initialized
        window.turnstileInitialized['{container_id}'] = true;

        // Handle HTMX events if HTMX is present
        if (window.htmx) {{
            form.addEventListener('htmx:beforeRequest', function(event) {{
                if (!isValidated && !isProcessing) {{
                    event.preventDefault();
                    isProcessing = true;
                    isHtmxSubmission = true;
                    originalEvent = event; // Store the original event
                    renderTurnstile();
                }}
            }});
        }}

        // Handle regular form submission
        form.addEventListener('submit', function(event) {{
            if (!isValidated && !isProcessing) {{
                event.preventDefault();
                isProcessing = true;
                isHtmxSubmission = false;
                originalEvent = event; // Store the original event
                renderTurnstile();
            }}
        }});

        function renderTurnstile() {{
            // Clear any existing widgets in this container first
            container.innerHTML = '';

            if (typeof turnstile === 'undefined') {{
                console.error('Turnstile API not loaded. Make sure to include the Turnstile script in your base template.');
                isProcessing = false;
                return;
            }}

            turnstile.render('#{container_id}', {{
                sitekey: '{site_key}',
                callback: function(token) {{
                    // Remove any existing inputs to avoid duplicates
                    const existingInputs = form.querySelectorAll('input[name="cf-turnstile-response"]');
                    existingInputs.forEach(input => input.remove());

                    // Create a new token input
                    const tokenInput = document.createElement('input');
                    tokenInput.type = 'hidden';
                    tokenInput.name = 'cf-turnstile-response';
                    tokenInput.value = token;
                    form.appendChild(tokenInput);

                    isValidated = true;
                    isProcessing = false;

                    // Continue form submission based on type
                    if (isHtmxSubmission && window.htmx) {{
                        // For HTMX forms, trigger the HTMX request
                        if (form.getAttribute('hx-post')) {{
                            htmx.trigger(form, 'htmx:beforeRequest');
                            setTimeout(function() {{
                                htmx.process(form);
                            }}, 50);
                        }}
                    }} else {{
                        // For regular forms, submit normally
                        const submitEvent = new Event('submit', {{bubbles: true, cancelable: true}});
                        form.dispatchEvent(submitEvent);
                        if (!submitEvent.defaultPrevented) {{
                            form.submit();
                        }}
                    }}
                }},
                'expired-callback': function() {{
                    isValidated = false;
                    isProcessing = false;
                }},
                'error-callback': function() {{
                    isValidated = false;
                    isProcessing = false;
                }}
            }});
        }}
    }});
    </script>
    """
    return mark_safe(html)


@register.simple_tag
def turnstile_script():
    """
    Renders the Cloudflare Turnstile script tag.

    This should be included in the head or at the end of the body of your base template.

    Usage:
        {% load turnstile_tags %}
        <html>
            <head>
                {% turnstile_script %}
            </head>
            <body>
                <!-- Your content here -->
            </body>
        </html>
    """
    html = """
    <script src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit" async defer></script>
    """
    return mark_safe(html)
