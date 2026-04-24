from django import template

register = template.Library()

@register.filter(name='filtro_texto')
def filtro_texto(valeu, arg=None):
    return value.upper()
