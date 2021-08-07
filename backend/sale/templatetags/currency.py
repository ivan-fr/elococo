from decimal import Decimal

from django import template
from django.conf import settings

from sale import get_amount

register = template.Library()


@register.filter
def deduce_tva(value):
    return "{:.2f}".format(Decimal(value) * settings.TVA_PERCENT * settings.BACK_TWO_PLACES)


@register.filter
def to_currency_decimal(value):
    return Decimal(value) * settings.BACK_TWO_PLACES


@register.filter
def to_currency(value):
    return "{:.2f}".format(Decimal(value) * settings.BACK_TWO_PLACES)


@register.simple_tag
def amount_with_delivery(order):
    return "{:.2f}".format(get_amount(order, with_delivery=True) * settings.BACK_TWO_PLACES)
