from abc import ABC
from decimal import Decimal

from django.db.models import F, Case, When, Value, Sum, OuterRef, Subquery, Exists
from django.db.models import PositiveSmallIntegerField, IntegerField
from django.db.models.functions import Ceil, Least
from django.utils.timezone import now
from django.db.models import Max, Min

from catalogue.forms import BASKET_MAX_QUANTITY_PER_FORM
from catalogue.models import Category

TVA_PERCENT = Decimal(20.)
BACK_TWO_PLACES = Decimal(10) ** -2
TVA = Decimal(120) * BACK_TWO_PLACES


def reduction_from_bdd():
    return Case(
        When(reduction_end__gte=now().today(), then=F('reduction')),
        default=Value(0)
    )


def price_exact(with_reduction=True):
    decimal_price = F('price')
    if with_reduction:
        reduction_percentage = Decimal(
            1.) - reduction_from_bdd() * BACK_TWO_PLACES
        return Ceil(decimal_price * reduction_percentage) * BACK_TWO_PLACES
    return decimal_price * BACK_TWO_PLACES


def price_exact_ht(with_reduction=True):
    price = price_exact(with_reduction)
    return Case(When(TTC_price=True, then=price * Decimal(100.) / (Decimal(100.) * TVA)), default=price)


def price_exact_ttc(with_reduction=True):
    price = price_exact(with_reduction)
    return Case(When(TTC_price=False, then=price * TVA), default=price)


def effective_quantity(data):
    return Least(data["quantity"], BASKET_MAX_QUANTITY_PER_FORM, F("stock"), output_field=PositiveSmallIntegerField())


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


def price_annotation_format(basket=None):
    price_exact_ttc_ = price_exact_ttc()
    price_exact_ht_ = price_exact_ht()
    my_dict = {"price_exact_ttc": price_exact_ttc_,
               "price_exact_ht": price_exact_ht_,
               "price_base_ttc": price_exact_ttc(with_reduction=False),
               "effective_reduction": reduction_from_bdd()}

    if basket is not None and bool(basket):
        my_dict["price_exact_ttc_with_quantity"] = total_price_per_product_from_basket(
            basket, price_exact_ttc_)
        my_dict["price_exact_ht_with_quantity"] = total_price_per_product_from_basket(
            basket, price_exact_ht_)
        my_dict["effective_basket_quantity"] = effective_quantity_per_product_from_basket(
            basket)

    return my_dict


def total_price_from_all_product():
    return Sum(F("price_exact_ttc_with_quantity")), Sum(F("price_exact_ht_with_quantity"))


def data_from_all_product():
    return Min("price_exact_ttc"), Max("price_exact_ttc")


def get_descendants_categories(with_products=True, include_self=False, **filters):
    if with_products:
        d1 = {"products__stock__gt": 0, "products__enable_sale": True}
    else:
        d1 = {}

    if include_self:
        d3 = {"depth__gte": OuterRef("depth")}
    else:
        d3 = {"depth__gt": OuterRef("depth")}

    return Category.objects.all().filter(
        path__startswith=OuterRef("path"),
        **d1, **d3, **filters
    ).values(
        'products__pk'
    ).distinct()


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
