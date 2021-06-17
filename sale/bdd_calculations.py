import datetime

from django.conf import settings
from django.db.models import Case, When, Q, F, ExpressionWrapper, DateTimeField, Count, OuterRef, Sum
from django.db.models.functions import Now

from catalogue.bdd_calculations import total_price_per_product_from_basket, price_exact_ht
from catalogue.models import Product
from sale.models import Promo, Ordered


def get_promo(basket, code):
    if code is None:
        return None

    try:
        return Promo.objects.filter(code=code).filter(
            (Q(startOfLife__lte=Now()) & Q(endOfLife__gte=Now())) | (Q(startOfLife=None) & Q(endOfLife=None)) |
            (Q(startOfLife__lte=Now()) & Q(endOfLife=None)) | (Q(startOfLife=None) & Q(endOfLife__gte=Now()))
        ).filter(
            max_time__gte=Count(Ordered.objects.filter(promo=OuterRef("code")), distinct=True),
            min_products_basket__lte=len(basket),
        ).annotate(
            price_exact_ht_with_quantity__sum=Case(
                When(min_ht=None, then=None), default=Product.objects.filter(slug__in=tuple(basket.keys())).annotate(
                    price_exact_ht_with_quantity=total_price_per_product_from_basket(
                        basket, price_exact_ht(with_reduction=True)
                    )
                ).aggregate(Sum("price_exact_ht_with_quantity")))
        ).filter(
            Q(min_ht__lte=F("price_exact_ht_with_quantity__sum")) | Q(min_ht=None)
        ).get()
    except Promo.DoesNotExist:
        raise None


def time_delta():
    return datetime.timedelta(minutes=settings.TIME_ORDERED_CLOSE_PAYMENT_TIME_BEFORE_END)


def effective_end_time_payment():
    return ExpressionWrapper(F("endOfLife") - time_delta(), DateTimeField())


def ordered_is_enable(delete=False):
    if delete:
        time_to_compare = Now()
        bool_to_have = False
    else:
        time_to_compare = Now() + time_delta()
        bool_to_have = True

    return Case(
        When(Q(endOfLife__gte=time_to_compare), then=bool_to_have),
        When(Q(endOfLife__lt=time_to_compare) & Q(payment_status=True), then=bool_to_have),
        default=not bool_to_have
    )


def default_ordered_annotation_format():
    my_dict = {"ordered_is_enable": ordered_is_enable(), "effective_end_time_payment": effective_end_time_payment(),
               "ordered_is_ready_to_delete": ordered_is_enable(delete=True)}
    return my_dict
