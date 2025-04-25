from django import template

register = template.Library()

@register.filter
def ends_with(value, suffix):
    return str(value).endswith(str(suffix))