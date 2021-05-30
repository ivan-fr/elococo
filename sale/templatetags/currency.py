from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def to_currency(value):
    return "{:.2f}".format(Decimal(value) / Decimal(100.))
