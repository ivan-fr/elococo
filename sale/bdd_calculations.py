from django.db.models import Case, When, Q
from django.utils.timezone import now


def ordered_is_enable():
    return Case(
        When(Q(endOfLife__lte=now()), then=True),
        When(Q(endOfLife__gt=now()) & Q(payment_status=True), then=True),
        default=False
    )


def default_ordered_annoation_format():
    my_dict = {"ordered_is_enable": ordered_is_enable()}
    return my_dict
