import datetime

from django.db.models import Case, When, Q, F, ExpressionWrapper, DateTimeField
from django.utils.timezone import now

from sale.models import TIME_ORDERED_CLOSE_PAYMENT_TIME_BEFORE_END


def time_delta():
    return datetime.timedelta(minutes=TIME_ORDERED_CLOSE_PAYMENT_TIME_BEFORE_END)


def effective_end_time_payment():
    return ExpressionWrapper(F("endOfLife") - time_delta(), DateTimeField())


def ordered_is_enable(delete=False):
    if delete:
        time_to_compare = now()
        bool_to_have = False
    else:
        time_to_compare = now() - time_delta()
        bool_to_have = True

    return Case(
        When(Q(endOfLife__gt=time_to_compare), then=bool_to_have),
        When(Q(endOfLife__lte=time_to_compare) & Q(payment_status=True), then=bool_to_have),
        default=not bool_to_have
    )


def default_ordered_annotation_format():
    my_dict = {"ordered_is_enable": ordered_is_enable(), "effective_end_time_payment": effective_end_time_payment(),
               "ordered_is_ready_to_delete": ordered_is_enable(delete=True)}
    return my_dict
