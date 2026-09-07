from django import template

register = template.Library()


@register.filter
def formfield(form, name):
    """Return a bound field by name — lets templates iterate a name list."""
    try:
        return form[name]
    except KeyError:
        return None
