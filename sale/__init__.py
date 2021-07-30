from decimal import Decimal


def get_amount(ordered, with_delivery=False, with_promo=True):
    if ordered.price_exact_ttc_with_quantity_sum_promo is not None and with_promo:
        amount = Decimal(ordered.price_exact_ttc_with_quantity_sum_promo)
    else:
        amount = Decimal(ordered.price_exact_ttc_with_quantity_sum)

    if with_delivery:
        if ordered.delivery_value is None:
            dv = Decimal(0)
        else:
            dv = Decimal(ordered.delivery_value)
        amount += dv

    return amount
