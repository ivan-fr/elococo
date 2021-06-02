from decimal import Decimal

from django import template

from catalogue.bdd_calculations import TVA_PERCENT

register = template.Library()


@register.filter
def deduce_tva(value):
    return "{:.2f}".format(Decimal(value) * TVA_PERCENT * Decimal(10) ** -2)


@register.filter
def to_currency(value):
    return "{:.2f}".format(Decimal(value) / Decimal(100.))
