import datetime

from django.db.models import Case, When, Q, F, ExpressionWrapper, DateTimeField
from django.utils.timezone import now

from sale.models import TIME_ORDERED_CLOSE_PAYMENT_TIME_BEFORE_END


def time_delta():
    return datetime.timedelta(minutes=TIME_ORDERED_CLOSE_PAYMENT_TIME_BEFORE_END)


def effective_end_time_payment():
    return ExpressionWrapper(F("endOfLife") - time_delta(), DateTimeField())


def ordered_is_enable():
    return Case(
        When(Q(endOfLife__gt=now() - time_delta()), then=True),
        When(Q(endOfLife__lte=now() - time_delta()) & Q(payment_status=True), then=True),
        default=False
    )


def default_ordered_annotation_format():
    my_dict = {"ordered_is_enable": ordered_is_enable(), "effective_end_time_payment": effective_end_time_payment()}
    return my_dict
