from decimal import Decimal

from django import template
from django.conf import settings

register = template.Library()


@register.filter
def deduce_tva(value):
    return "{:.2f}".format(Decimal(value) * settings.TVA_PERCENT * settings.BACK_TWO_PLACES)


@register.filter
def to_currency(value):
    return "{:.2f}".format(Decimal(value) / Decimal(100.))
