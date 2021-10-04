from django import template

register = template.Library()


@register.filter
def sub(value, arg=None):
    if arg is None:
        arg = 0
    return int(value) - int(arg)
