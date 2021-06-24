from abc import ABC
from decimal import Decimal

from django.conf import settings
from django.db.models import F, Case, When, Value, Sum, OuterRef, Subquery, Exists
from django.db.models import FloatField
from django.db.models import Max, Min
from django.db.models import PositiveSmallIntegerField
from django.db.models.functions import Cast
from django.db.models.functions import Ceil, Least, Floor, Greatest
from django.utils.timezone import now

from catalogue.models import Category, Product, ProductToProduct
from sale.models import OrderedProduct


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
    return Least(data["quantity"], settings.BASKET_MAX_QUANTITY_PER_FORM, F("effective_stock"),
                 output_field=PositiveSmallIntegerField())


def effective_quantity_per_product_from_basket(basket):
    whens = (When(
        slug=slug,
        then=effective_quantity(data)
    ) for slug, data in basket.items())
    return Case(
        *whens,
        default=Value(0)
    )


def get_quantity_from_basket_box(basket):
    whens = (
        When(
            pk=slug, then=F("intermediate_quantity") * Least(
                data["quantity"],
                settings.BASKET_MAX_QUANTITY_PER_FORM,
                F("effective_stock"),
                output_field=PositiveSmallIntegerField()
            )
        ) for slug, data in basket.items()
    )

    cases = Case(*whens, default=Value(0))

    return {
        "quantity_from_basket_box": Case(
            When(
                Exists(
                    Product.objects.filter(
                        slug__in=basket.keys(), box__elements=OuterRef("pk")
                    )
                ),
                then=SQSum(
                    Product.objects.filter(
                        slug__in=basket.keys(), box__elements=OuterRef("pk")
                    ).annotate(
                        intermediate_quantity=Subquery(
                            ProductToProduct.objects.filter(
                                box__pk=OuterRef("pk"),
                                elements__pk=OuterRef(OuterRef("pk"))
                            ).values("quantity")
                        ),
                        effective_stock=effective_stock()
                    ).annotate(
                        total_intermediate_quantity=cases
                    ).values("total_intermediate_quantity"),
                    "total_intermediate_quantity"
                )
            ),
            default=Value(0),
            output_field=PositiveSmallIntegerField()
        )
    }


def get_stock_with_basket():
    return {
        "post_effective_stock_with_basket": Greatest(
            F("effective_stock") - F("quantity_from_basket_box"), 0
        )
    }


def post_effective_basket_quantity():
    return {
        "post_effective_basket_quantity": Case(
            When(
                effective_stock__gte=F("quantity_from_basket_box") + F("effective_basket_quantity"),
                then=F("effective_basket_quantity")
            ), default=F("effective_stock") - F("quantity_from_basket_box") - F("effective_basket_quantity"),
            output_field=PositiveSmallIntegerField()
        )
    }


def total_price_per_product_from_basket(f):
    return F(f) * F("post_effective_basket_quantity")


def effective_stock():
    return Case(
        When(
            Exists(
                Product.objects.filter(
                    elements__box__pk=OuterRef("pk")
                )
            ),
            then=SQMin(
                Product.objects.filter(
                    elements__box__pk=OuterRef("pk")
                ).annotate(
                    intermediate_quantity=Subquery(
                        ProductToProduct.objects.filter(box__pk=OuterRef(OuterRef("pk")),
                                                        elements__pk=OuterRef("pk")).values("quantity")
                    )
                ).annotate(
                    stock_for_box=Floor(
                        F("stock") / F("intermediate_quantity"),
                        output_field=PositiveSmallIntegerField()
                    )
                ).values("stock_for_box"),
                "stock_for_box"
            )
        ),
        default=F("stock"),
        output_field=PositiveSmallIntegerField()
    )


def stock_details(sold=False):
    return SQSum(
        OrderedProduct.objects.filter(
            to_product__pk=OuterRef("pk"),
            from_ordered__payment_status=sold
        ).values("quantity"),
        "quantity"
    )


def annotate_effective_stock():
    return {
        "effective_stock": effective_stock(),
        "stock_sold": stock_details(True),
    }


def price_annotation_format(basket=None):
    price_exact_ttc_ = price_exact_ttc()
    price_exact_ht_ = price_exact_ht()
    my_dict = {
        "price_exact_ttc": price_exact_ttc_,
        "price_exact_ht": price_exact_ht_,
        "price_base_ttc": price_exact_ttc(with_reduction=False),
        "effective_reduction": reduction_from_bdd()
    }

    if basket is not None and bool(basket):
        my_dict["effective_basket_quantity"] = effective_quantity_per_product_from_basket(basket)
    return my_dict


def post_price_annotation_format():
    my_dict = {"price_exact_ttc_with_quantity": total_price_per_product_from_basket("price_exact_ttc"),
               "price_exact_ht_with_quantity": total_price_per_product_from_basket("price_exact_ht")}
    return my_dict


def cast_annotate_to_float(dict_, key):
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


def get_descendants_categories(include_self=False, **filters):
    if include_self:
        d3 = {"depth__gte": OuterRef("depth")}
    else:
        d3 = {"depth__gt": OuterRef("depth")}

    qs = Category.objects.all()

    qs = qs.filter(
        path__startswith=OuterRef("path"),
        **d3, **filters
    )

    return qs


def get_descendants_products(with_products=True, include_self=False, **filters):
    if include_self:
        d3 = {"categories__depth__gte": OuterRef("depth")}
    else:
        d3 = {"categories__depth__gt": OuterRef("depth")}

    qs = Product.objects.all().annotate(
        **annotate_effective_stock()
    )

    if with_products:
        qs = qs.filter(
            effective_stock__gt=0, enable_sale=True
        )

    qs = qs.filter(
        categories__path__startswith=OuterRef("path"), **d3, **filters
    ).values(
        'pk'
    ).distinct()

    return qs


class SQSum(Subquery, ABC):
    def __init__(self, queryset, column, output_field=None, **extra):
        self.template = '(SELECT SUM({}) FROM (%(subquery)s) _min)'.format(column)
        super(SQSum, self).__init__(queryset, output_field, **extra)

    output_field = PositiveSmallIntegerField()


class SQMin(Subquery, ABC):
    def __init__(self, queryset, column, output_field=None, **extra):
        self.template = '(SELECT min({}) FROM (%(subquery)s) _min)'.format(column)
        super(SQMin, self).__init__(queryset, output_field, **extra)

    output_field = PositiveSmallIntegerField()


class SQCount(Subquery, ABC):
    template = "(SELECT COUNT(*) FROM (%(subquery)s) _count)"
    output_field = PositiveSmallIntegerField()


def get_related_products(selected_category, products_queryset=None):
    related_products = None
    if products_queryset is not None:
        related_products = products_queryset.filter(
            categories__slug__in=Subquery(
                Category.objects.filter(
                    path__startswith=selected_category.path,
                    depth__gte=selected_category.depth
                ).values("slug")
            )
        ).distinct()

    return related_products


def filled_category(limit, selected_category=None, products_queryset=None):
    filled_category_ = Category.get_root_nodes().filter(
        Exists(get_descendants_products(include_self=True))
    ).annotate(products_count__sum=SQCount(get_descendants_products(include_self=True)))[:limit]

    dict_ = {'filled_category': filled_category_, "selected_category_root": None, "related_products": None,
             "selected_category": None, "filter_list": None}

    if selected_category is not None:
        dict_["selected_category_root"] = Category.objects.filter(pk__in=filled_category_).filter(
            Exists(
                get_descendants_categories(
                    include_self=True,
                    slug=selected_category
                )
            )
        )

        selected_category_root = dict_["selected_category_root"]
        try:
            obj = selected_category_root.get()
            selected_category = Category.objects.filter(slug=selected_category).get()
            dict_["related_products"] = get_related_products(selected_category, products_queryset)

            annotated_list = Category.get_tree(
                obj
            ).filter(
                depth__lte=2
            ).annotate(
                products_count__sum=SQCount(
                    get_descendants_products(include_self=True)
                )
            )

            dict_["filter_list"] = Category.get_annotated_list_qs(
                annotated_list
            )

            dict_["selected_category_root"] = obj
            dict_["selected_category"] = selected_category
        except selected_category_root.model.DoesNotExist:
            dict_["selected_category_root"] = None

    return dict_
