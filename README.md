# Django Turnstile HTMX

A Django app for integrating Cloudflare Turnstile CAPTCHA protection with support for HTMX.

## Features

- Easy integration with Django views and templates
- Support for both regular forms and HTMX requests
- Server-side validation via decorator
- Simple template tag for adding Turnstile to forms

## Installation

1. Install the package from PyPI:
   ```bash
   pip install django-turnstile-htmx
   ```

2. Add the app to `INSTALLED_APPS` in your `settings.py`:
   ```python
   INSTALLED_APPS = [
       # ...
       'turnstile_htmx.apps.TurnstileHtmxConfig',
       # ...
   ]
   ```
3. Configure Cloudflare Turnstile keys:
   ```python
   CLOUDFLARE_TURNSTILE_SITE_KEY = 'your-site-key-here'
   CLOUDFLARE_TURNSTILE_SECRET_KEY = 'your-secret-key-here'
   ```

## Usage

1. Add script to base template:
   ```html
   {% load turnstile_tags %}
   <head>
     {% turnstile_script %}
   </head>
   ```

2. Add Turnstile field to forms:
   ```html
   {% load turnstile_tags %}

   <!-- Regular form -->
   <form method="post">
     {% csrf_token %}
     {{ form.as_p }}
     {% turnstile_field %}
     <button type="submit">Submit</button>
   </form>

   <!-- HTMX form -->
   <form hx-post="{% url 'your-view' %}" hx-target="#result">
     {% csrf_token %}
     <input type="email" name="email" required>
     {% turnstile_field %}
     <button type="submit">Subscribe</button>
   </form>
   ```

3. Protect views with decorator:
   ```python
   from turnstile_htmx.decorators import turnstile_protected

   @turnstile_protected
   def contact_form_view(request):
       # Process form - validation already happened!
       return render(request, 'contact.html')
   ```

## API Reference

### Template Tags

- `{% turnstile_field %}` - Renders the Turnstile widget
  - Parameters: `container_id` (optional), `site_key` (optional)

- `{% turnstile_script %}` - Renders the Turnstile script tag

### Decorators

- `@turnstile_protected` - Validates Turnstile token on POST requests
  - Parameters: `error_template` (optional)

## Examples

### Contact Form

```html
<!-- Template -->
{% extends 'base.html' %}
{% load turnstile_tags %}

{% block content %}
  <form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    {% turnstile_field %}
    <button type="submit">Send</button>
  </form>
{% endblock %}
```

```python
# View
from turnstile_htmx.decorators import turnstile_protected

@turnstile_protected
def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('success')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})
```

### Customization

```python
# Custom error template
@turnstile_protected(error_template='<div class="alert">Verification failed!</div>')
def my_view(request):
    # ...

# Custom container ID
{% turnstile_field container_id="my-turnstile" %}
```

## Troubleshooting

- **Widget not appearing**: Check that `{% turnstile_script %}` is included and site key is correct
- **Validation failing**: Verify secret key and check browser console for errors
- **HTMX issues**: Ensure HTMX is loaded before Turnstile script

## License

MIT
