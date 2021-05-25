from datetime import date
from django.db.models import F, Count, Case, When, Value, Sum
from django.db.models.functions import Cast, Ceil
from django.db.models import FloatField
from catalogue.models import Category


def price_from_bdd():
    return Cast(F('price'), FloatField()) / 100.


def reduction_from_bdd():
    return Case(
        When(reduction_end__gte=date.today(), then=F('reduction')),
        default=Value(0)
    )


def price_exact_from_bdd():
    decimal_price = Cast(F('price'), FloatField())
    reduction_percentage = 1. - Cast(reduction_from_bdd(), FloatField()) / 100.
    return Ceil(decimal_price * reduction_percentage) / 100.


def total_price_per_product_from_basket(basket):
    whens = (When(slug=slug, then=price_exact_from_bdd() * int(data["quantity"])) for slug, data in basket.items())
    return Case(
        *whens,
        default=Value(0.)
    )


def price_annotation_format(basket=None):
    my_dict = {"exact_price": price_exact_from_bdd(),
               "base_price": price_from_bdd(),
               "effective_reduction": reduction_from_bdd()}

    if basket is not None and bool(basket):
        my_dict["exact_price_with_quantity"] = total_price_per_product_from_basket(basket)

    return my_dict


def total_price_from_all_product():
    return Sum(F("exact_price_with_quantity"))


def filled_category(limit):
    return {'filled_category': Category.objects.annotate(Count('product', distinct=True)).filter(
        product__count__gt=0).order_by('-product__count', 'category')[:limit]}
