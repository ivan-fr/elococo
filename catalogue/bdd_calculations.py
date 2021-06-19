from abc import ABC
from decimal import Decimal

from django.conf import settings
from django.db.models import F, Case, When, Value, Sum, OuterRef, Subquery, Exists
from django.db.models import FloatField
from django.db.models import Max, Min
from django.db.models import PositiveSmallIntegerField, IntegerField
from django.db.models.functions import Cast
from django.db.models.functions import Ceil, Least
from django.utils.timezone import now

from catalogue.models import Category, Product


def reduction_from_bdd():
    return Case(
        When(reduction_end__gte=now().today(), then=F('reduction')),
        default=Value(0)
    )


def price_exact(with_reduction=True):
    decimal_price = F('price')
    if with_reduction:
        reduction_percentage = Decimal(
            1.) - reduction_from_bdd() * settings.BACK_TWO_PLACES
        return Ceil(decimal_price * reduction_percentage) * settings.BACK_TWO_PLACES
    return decimal_price * settings.BACK_TWO_PLACES


def price_exact_ht(with_reduction=True):
    price = price_exact(with_reduction)
    return Case(When(TTC_price=True, then=price * Decimal(100.) / (Decimal(100.) * settings.TVA)), default=price)


def price_exact_ttc(with_reduction=True):
    price = price_exact(with_reduction)
    return Case(When(TTC_price=False, then=price * settings.TVA), default=price)


def range_ttc(with_reduction=True):
    price = price_exact(with_reduction)
    return When(
        Case(When(TTC_price=False, then=price * settings.TVA), default=price)
    )


def effective_quantity(data):
    return Least(data["quantity"], settings.BASKET_MAX_QUANTITY_PER_FORM, effective_stock(),
                 output_field=PositiveSmallIntegerField())


def effective_quantity_per_product_from_basket(basket):
    whens = (When(
        slug=slug, then=effective_quantity(data)
    ) for slug, data in basket.items())
    return Case(
        *whens,
        default=Value(0)
    )


def total_price_per_product_from_basket(basket, price_exact_ttc_):
    whens = (When(
        slug=slug, then=price_exact_ttc_ * effective_quantity(data)
    ) for slug, data in basket.items())
    return Case(
        *whens,
        default=Value(Decimal(0.))
    )


def effective_stock(relative=""):
    sub = Subquery(
        Product.objects.filter(
            to_product__from_product=OuterRef(relative + "pk")
        ).annotate(
            stock_for_parent=F("to_product__quantity") // F("stock")
        ).aggregate(
            Min("stock_for_parent")
        ).values("stock_for_parent__min")
    )

    return Case(
        When(
            Exists(
                Product.objects.filter(
                    to_product__from_product=OuterRef(relative + "pk")
                )
            ),
            then=sub
        ),
        default=F("stock"),
        output_field=PositiveSmallIntegerField()
    )


def price_annotation_format(basket=None):
    price_exact_ttc_ = price_exact_ttc()
    price_exact_ht_ = price_exact_ht()
    my_dict = {"price_exact_ttc": price_exact_ttc_,
               "price_exact_ht": price_exact_ht_,
               "price_base_ttc": price_exact_ttc(with_reduction=False),
               "effective_reduction": reduction_from_bdd(),
               "effective_stock": effective_stock()}

    if basket is not None and bool(basket):
        my_dict["price_exact_ttc_with_quantity"] = total_price_per_product_from_basket(
            basket, price_exact_ttc_)
        my_dict["price_exact_ht_with_quantity"] = total_price_per_product_from_basket(
            basket, price_exact_ht_)
        my_dict["effective_basket_quantity"] = effective_quantity_per_product_from_basket(
            basket)
    return my_dict


def cast_annotate_to_decimal(dict_, key):
    dict_[key] = Cast(dict_[key], output_field=FloatField())


def total_price_from_all_product(promo=None):
    dict_ = {"price_exact_ttc_with_quantity__sum": Sum("price_exact_ttc_with_quantity"),
             "price_exact_ht_with_quantity__sum": Sum("price_exact_ht_with_quantity")}
    if promo is not None:
        if promo.type == "pe":
            promo_percentage = Decimal(1.) - promo.value * settings.BACK_TWO_PLACES
            ht_promo = promo_percentage * Sum("price_exact_ht_with_quantity")
            dict_.update({
                "price_exact_ht_with_quantity_promo__sum": ht_promo,
                "price_exact_ttc_with_quantity_promo__sum": ht_promo * settings.TVA,
            })
        elif promo.type == "cu":
            ht_promo = Sum("price_exact_ht_with_quantity") - Decimal(promo.value)
            dict_.update({
                "price_exact_ht_with_quantity_promo__sum": ht_promo,
                "price_exact_ttc_with_quantity_promo__sum": ht_promo * settings.TVA,
            })

    return dict_


def data_from_all_product():
    return Min("price_exact_ttc"), Max("price_exact_ttc")


def get_descendants_categories(with_products=True, include_self=False, **filters):
    if with_products:
        d1 = {"products__effective_stock__gt": 0, "products__enable_sale": True}
    else:
        d1 = {}

    if include_self:
        d3 = {"depth__gte": OuterRef("depth")}
    else:
        d3 = {"depth__gt": OuterRef("depth")}

    r = Category.objects.all()

    if with_products:
        r = r.annotate(products__effective_stock=effective_stock("products__"))

    r = r.filter(
        path__startswith=OuterRef("path"),
        **d1, **d3, **filters
    ).values(
        'products__pk'
    ).distinct()

    return r


class SQSum(Subquery, ABC):
    template = "(SELECT COUNT(*) FROM (%(subquery)s) _count)"
    output_field = IntegerField()


def filled_category(limit, selected_category=None, products_queryset=None):
    filled_category_ = Category.get_root_nodes().filter(
        Exists(get_descendants_categories(include_self=True))
    ).annotate(products_count__sum=SQSum(get_descendants_categories(include_self=True)))[:limit]

    dict_ = {'filled_category': filled_category_, "selected_category_root": None, "related_products": None,
             "selected_category": None, "filter_list": None}

    if selected_category is not None:
        dict_["selected_category_root"] = Category.objects.filter(pk__in=filled_category_).filter(
            Exists(
                get_descendants_categories(
                    with_products=False,
                    include_self=True,
                    slug=selected_category
                )
            )
        )

        selected_category_root = dict_["selected_category_root"]
        try:
            obj = selected_category_root.get()
            selected_category = Category.objects.filter(
                slug=selected_category).get()
            if products_queryset is not None:
                related_products = products_queryset.filter(
                    categories__slug__in=Subquery(
                        Category.objects.filter(
                            path__startswith=selected_category.path,
                            depth__gte=selected_category.depth
                        ).values("slug")
                    )
                ).distinct()

                dict_["related_products"] = related_products
            else:
                dict_["related_products"] = None

            annotated_lsit = Category.get_tree(
                obj
            ).filter(
                depth__lte=2
            ).annotate(
                products_count__sum=SQSum(
                    get_descendants_categories(include_self=True))
            )

            dict_["filter_list"] = Category.get_annotated_list_qs(
                annotated_lsit)

            dict_["selected_category_root"] = obj
            dict_["selected_category"] = selected_category
        except selected_category_root.model.DoesNotExist:
            dict_["selected_category_root"] = None

    return dict_
